# 34. 设计 API 网关 (API Gateway)

## 题目

设计一个高性能 API 网关系统，作为所有微服务的统一入口，提供路由、认证、限流、监控、协议转换等功能。类似 Kong、APISIX、AWS API Gateway。

---

## 需求澄清

### 功能性需求 (Functional Requirements)

- 请求路由：根据 URL、Header、Method 将请求路由到对应的后端服务
- 认证与授权：支持 JWT、OAuth2、API Key、mTLS 多种认证方式
- 速率限制（Rate Limiting）：按用户、IP、API 维度限流
- 负载均衡：支持轮询、加权轮询、最少连接、一致性哈希
- 请求/响应转换：修改 Header、Body 转换、协议转换
- API 版本管理：支持多版本 API 共存
- 请求聚合（BFF）：合并多个后端请求为一个响应
- 熔断与降级：后端服务不可用时自动熔断
- 缓存：对可缓存的响应进行缓存
- 日志与监控：记录所有请求，提供实时监控和告警
- 插件系统：允许自定义插件扩展功能

### 非功能性需求 (Non-functional Requirements)

| 指标 | 要求 |
|------|------|
| 吞吐量 | 100,000+ QPS 单节点 |
| 延迟 | P99 < 10ms（网关增加的开销） |
| 可用性 | 99.999%（五九） |
| 热更新 | 配置变更无需重启网关 |
| 扩展性 | 水平扩展，无单点瓶颈 |

### 容量估算 (Capacity Estimation)

假设：
- 日活跃用户：1000万，每用户每天 API 调用：100次
- 每日总请求：10亿，平均 QPS ≈ 11,574
- 峰值 QPS（3倍）：约 35,000 QPS
- 网关节点数：10台（每节点支持 100K QPS）

---

## API 设计

### 网关管理 API

```
# 路由管理
POST /admin/routes
{
  "name": "user-service",
  "uri": "/api/v1/users/*",
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "host": "api.myapp.com",
  "upstream": {
    "type": "roundrobin",
    "nodes": {
      "user-service-1:8080": 1,
      "user-service-3:8080": 2
    },
    "timeout": { "connect": 6000, "send": 6000, "read": 6000 }
  },
  "plugins": {
    "rate-limiting": { "rate": 100, "burst": 200, "key": "consumer_id" },
    "jwt-auth": {}
  }
}

GET    /admin/routes
GET    /admin/routes/:id
PUT    /admin/routes/:id
DELETE /admin/routes/:id

# 上游服务管理
POST   /admin/upstreams
GET    /admin/upstreams

# Consumer 管理
POST   /admin/consumers
GET    /admin/consumers
POST   /admin/consumers/:username/credentials

# 插件管理
POST   /admin/plugins
GET    /admin/plugins
PUT    /admin/plugins/:id
```

### 数据面请求流程

```
Client Request:
  GET https://api.myapp.com/api/v1/users/123
  Authorization: Bearer eyJhbGciOi...

Gateway 转发到后端:
  GET http://user-service-1:8080/users/123
  X-Request-Id: req-abc-123
  X-Consumer-Id: consumer-456
  X-Forwarded-For: 192.168.1.100
```

---

## 数据模型

### 核心表结构

```sql
CREATE TABLE routes (
    id              UUID PRIMARY KEY,
    name            VARCHAR(255) UNIQUE NOT NULL,
    methods         TEXT[],
    hosts           TEXT[],
    uris            TEXT[],
    strip_uri       BOOLEAN DEFAULT TRUE,
    priority        INTEGER DEFAULT 0,
    service_id      UUID REFERENCES services(id),
    upstream_id     UUID REFERENCES upstreams(id),
    enabled         BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_routes_enabled ON routes(enabled);

CREATE TABLE upstreams (
    id              UUID PRIMARY KEY,
    name            VARCHAR(255) UNIQUE NOT NULL,
    algorithm       VARCHAR(20) DEFAULT 'round-robin',
    hash_on         VARCHAR(20) DEFAULT 'none',
    slots           INTEGER DEFAULT 10000,
    health_check    JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE upstream_nodes (
    id              UUID PRIMARY KEY,
    upstream_id     UUID NOT NULL REFERENCES upstreams(id),
    host            VARCHAR(255) NOT NULL,
    port            INTEGER NOT NULL,
    weight          INTEGER DEFAULT 1,
    status          VARCHAR(20) DEFAULT 'active',
    healthy         BOOLEAN DEFAULT TRUE,
    last_checked_at TIMESTAMP
);

CREATE TABLE services (
    id              UUID PRIMARY KEY,
    name            VARCHAR(255) UNIQUE NOT NULL,
    protocol        VARCHAR(20) DEFAULT 'http',
    host            VARCHAR(255) NOT NULL,
    port            INTEGER NOT NULL,
    retries         INTEGER DEFAULT 3,
    connect_timeout INTEGER DEFAULT 6000,
    send_timeout    INTEGER DEFAULT 6000,
    read_timeout    INTEGER DEFAULT 6000,
    enabled         BOOLEAN DEFAULT TRUE
);

CREATE TABLE plugins (
    id              UUID PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    scope           VARCHAR(20) NOT NULL,  -- global | route | service | consumer
    scope_id        UUID,
    config          JSONB NOT NULL,
    enabled         BOOLEAN DEFAULT TRUE,
    priority        INTEGER DEFAULT 0
);

CREATE INDEX idx_plugins_scope ON plugins(scope, scope_id);

-- 请求日志 (ClickHouse)
CREATE TABLE request_logs (
    timestamp       DateTime,
    request_id      String,
    route_id        String,
    consumer_id     String,
    method          String,
    uri             String,
    status_code     UInt16,
    latency_ms      UInt32,
    upstream_latency_ms UInt32,
    client_ip       String
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (timestamp, route_id)
TTL timestamp + INTERVAL 30 DAY;
```

---

## 高层次架构

### 系统架构图

```
                              ┌─────────────┐
                              │   DNS / CDN │
                              └──────┬──────┘
                                     │
                         ┌───────────▼───────────┐
                         │   L4 Load Balancer    │
                         │ (HAProxy / AWS NLB)   │
                         └───────────┬───────────┘
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     API Gateway Cluster (Data Plane)                  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Gateway Node 1  │  │  Gateway Node 2  │  │  Gateway Node 3  │  │
│  │                  │  │                  │  │                  │  │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │
│  │ │Router(Radix) │ │  │ │Router(Radix) │ │  │ │Router(Radix) │ │  │
│  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │
│  │ ┌──────▼───────┐ │  │ ┌──────▼───────┐ │  │ ┌──────▼───────┐ │  │
│  │ │Plugin Chain  │ │  │ │Plugin Chain  │ │  │ │Plugin Chain  │ │  │
│  │ │ Auth→Limit→  │ │  │ │ Auth→Limit→  │ │  │ │ Auth→Limit→  │ │  │
│  │ │ Trans→Proxy  │ │  │ │ Trans→Proxy  │ │  │ │ Trans→Proxy  │ │  │
│  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │ └──────┬───────┘ │  │
│  │ ┌──────▼───────┐ │  │ ┌──────▼───────┐ │  │ ┌──────▼───────┐ │  │
│  │ │Load Balancer │ │  │ │Load Balancer │ │  │ │Load Balancer │ │  │
│  │ └──────────────┘ │  │ └──────────────┘ │  │ └──────────────┘ │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼─────────────────────┼──────────────────────┼────────────┘
            │                     │                      │
            ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Backend Microservices                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │User Svc  │  │Order Svc │  │Payment   │  │Catalog   │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                     Control Plane (管理平面)                           │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────────────────────────┐       │
│  │ Admin API    │───▶│ Configuration Store (etcd/PostgreSQL) │       │
│  └──────────────┘    └──────────────┬───────────────────────┘       │
│                                     │                                │
│                    ┌────────────────▼───────────────────────┐       │
│                    │ Config Watcher (etcd Watch / 版本号轮询) │       │
│                    │ 热更新：配置变更实时推送到所有Gateway节点  │       │
│                    └────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. 高性能路由匹配 — Radix Tree (基数树)

```
路由表:
  GET    /api/v1/users
  GET    /api/v1/users/:id
  POST   /api/v1/users
  GET    /api/v1/orders/:id
  GET    /health

Radix Tree 结构:
                    root
                     │
          ┌──────────┼──────────┐
          │          │          │
          GET        POST       GET
          │          │          │
         /api        /api       /health → route{health}
          │           │
         /v1         /v1
          │           │
    ┌─────┴─────┐    /users → route{POST /v1/users}
    │           │
  /users      /orders
    │           │
  ┌─┴──┐      :id → route{GET /orders/:id}
  │    │
GET   :id
  │    │
route route{GET /users/:id}
{GET
 /users}
```

**路由匹配性能对比：**

| 方法 | 时间复杂度 | 说明 |
|------|-----------|------|
| 线性遍历 | O(N) | 最差方案 |
| HashMap | O(1) | 但无法处理 :id 参数 |
| 正则表达式 | O(N*M) | 灵活但性能差 |
| **Radix Tree** | **O(K)** | **K=路径长度，最优方案** |

### 2. 插件链与责任链模式

```
请求处理通过插件链:

   Client Request
        │
        ▼
┌───────────────────┐
│ 1. Rate Limiting  │ ← 速率限制 (最先执行, 快速拒绝)
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 2. Authentication │ ← JWT / API Key 认证
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 3. Authorization  │ ← ACL / RBAC 权限检查
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 4. Transform      │ ← 请求转换 (Header/Body)
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 5. Proxy → Upstream│ ← 转发到后端服务
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 6. Response Trans │ ← 响应转换
└────────┬──────────┘
         ▼
┌───────────────────┐
│ 7. Log & Metrics  │ ← 记录日志指标
└────────┬──────────┘
         ▼
   Client Response
```

**插件链实现：**

```go
type Plugin interface {
    Name() string
    Priority() int
    Access(ctx *Context) error
    Log(ctx *Context) error
}

type PluginChain struct {
    plugins []Plugin
}

func (pc *PluginChain) Execute(ctx *Context) error {
    for _, plugin := range pc.plugins {
        if err := plugin.Access(ctx); err != nil {
            ctx.AbortWithError(err)
            return err
        }
        if ctx.Aborted() {
            break
        }
    }
    return nil
}
```

### 3. 限流算法对比

| 算法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 固定窗口 | 每秒重置计数器 | 实现简单 | 临界点突发问题 |
| 滑动窗口 | 按小窗口滑动统计 | 平滑 | 内存较高 |
| **令牌桶** | **恒定速率放令牌** | **允许短时突发** | **参数调优** |
| 漏桶 | 请求队列恒定流出 | 绝对平滑 | 无法突发 |

**推荐: 令牌桶 (Token Bucket)**

```lua
-- Redis Lua 原子令牌桶实现
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or burst
local last_refill = tonumber(bucket[2]) or now

local elapsed = (now - last_refill) / 1000
tokens = math.min(burst, tokens + elapsed * rate)
last_refill = now

local allowed = tokens >= requested
if allowed then tokens = tokens - requested end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
redis.call('EXPIRE', key, math.ceil(burst / rate) + 1)

return {allowed and 1 or 0, tokens}
```

### 4. 负载均衡算法对比

| 算法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| Round Robin | 后端服务同构 | 实现简单，分布均匀 | 不考虑服务能力差异 |
| Weighted RR | 后端异构 | 按权重分配 | 需要合理设置权重 |
| Least Connections | 请求耗时不一 | 动态均衡 | 需要维护连接计数 |
| Consistent Hash | 有状态服务/缓存 | 节点变化影响小 | 可能不均衡 |
| EWMA | 自动感知延迟 | 自适应 | 实现复杂 |

### 5. 健康检查与熔断

```
健康检查策略:

主动检查 (Active Health Check):
  Gateway 定期发送探测请求到后端 (/health endpoint)
  间隔: 10s, 超时: 1s
  阈值: 连续3次成功→healthy, 连续3次失败→unhealthy

被动检查 (Passive Health Check):
  根据实际请求结果判断
  连续3次5xx → unhealthy
  连续3次2xx → healthy (恢复)

熔断器状态机:

      ┌──────────┐  连续失败>=阈值  ┌──────────┐
      │  CLOSED  │ ────────────────▶ │   OPEN    │
      │ (正常)   │                   │ (快速失败) │
      └──────────┘                   └─────┬─────┘
           ▲                               │
           │                         超时到期
           │                               │
           │                        ┌──────▼──────┐
           │      探测成功           │  HALF-OPEN  │
           └──────────────────────── │  (探测恢复)  │
                                     └─────────────┘
```

### 6. 分布式限流策略

```
多网关节点限流需要在全局范围内准确计数:

方案1: 集中式Redis (推荐)
  所有节点共享同一Redis，令牌桶状态全局共享
  延迟: 每次限流判断需1次Redis网络往返(~1ms)

方案2: 本地+同步 (混合)
  每个节点本地分配 rate/N 额度
  后台线程定期从全局计数器领取新额度
  适合对精确度要求略低的场景

方案3: 一致性哈希路由
  L4 LB使用IP Hash，同一用户请求总到同一节点
  每节点独立限流 = rate/N
```

---

## 扩展性与高可用

### 1. 无状态设计

```
核心原则: 网关节点不保存任何会话状态

状态外置:
  - 配置: etcd / PostgreSQL (Watch机制实时更新)
  - 限流计数: Redis (原子操作)
  - 认证Token: 无状态JWT (本地验证, 无需查询)
  - 缓存: 本地LRU + Redis二级

好处: 任意节点处理任意请求, 扩缩容无需迁移, 宕机无数据丢失
```

### 2. 热更新机制

```
Config Change Flow:

  Admin API → etcd/DB (写入新配置)
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    Watcher    Watcher    Watcher  (etcd Watch / 长轮询)
       │          │          │
       ▼          ▼          ▼
   Node1重建  Node2重建  Node3重建
   Radix Tree 路由表 (无需重启, 路由切换原子操作)
```

### 3. 故障处理

| 故障 | 影响 | 恢复 |
|------|------|------|
| 网关节点宕机 | LB自动摘除, 新请求路由到其他节点 | 自动恢复 |
| etcd故障 | 新配置无法下发, 现有配置继续工作 | etcd集群自动failover |
| Redis故障 | 限流策略降级为本地限流或放行 | Sentinel自动切换 |
| 后端服务宕机 | 健康检查发现, 熔断保护 | 后端恢复后自动加入 |

### 4. 监控与可观测性

```
关键监控指标:
┌──────────────────┬─────────────────────────┐
│ 指标              │ 告警阈值                 │
├──────────────────┼─────────────────────────┤
│ 请求QPS          │ 监控趋势, 异常突增        │
│ P99延迟          │ > 50ms (网关内部)        │
│ 上游P99延迟       │ > 500ms                 │
│ 错误率(5xx)      │ > 1%                   │
│ 限流拒绝数        │ > 1000/min             │
│ 熔断器打开数       │ > 0 (需要排查)         │
│ 网关节点健康       │ 任意节点不可用           │
└──────────────────┴─────────────────────────┘
```

### 5. 安全设计

- **传输层:** TLS 1.3 终结在网关
- **认证:** 支持 JWT(本地验证)、OAuth2(代理)、mTLS(双向)
- **防御:** IP黑白名单、WAF规则、请求大小限制、Header注入防护
- **敏感数据:** 不记录Authorization Header、密码等敏感字段

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 路由匹配 | Radix Tree (O(K)复杂度, 比正则快100x+) |
| 限流 | 令牌桶算法 (Redis + Lua 原子操作) |
| 负载均衡 | 加权轮询 + 健康检查 + 熔断 |
| 扩展性 | 无状态设计, 水平扩展, 热更新配置 |
| 高可用 | 多节点 + etcd集群 + Redis Sentinel |
| 协议转换 | HTTP/1.1 ↔ HTTP/2 ↔ gRPC |

**CAP 取舍：** API 网关是 AP 系统（可用性 + 分区容错）。网关的核心职责是"让请求通过"，在发生网络分区时宁可放宽限流策略或跳过非关键插件，也绝不能因为一致性检查导致请求被拒绝。限流计数可以略微不精确，但请求路由必须可用。

**关键设计权衡：**
1. **高性能 vs 功能丰富:** 网关处理路径极简，插件链可插拔以控制延迟
2. **精确限流 vs 低延迟:** 使用 Redis 集中限流增加 ~1ms 延迟 vs 本地近似限流零延迟
3. **通用网关 vs BFF:** 通用网关适合标准化API，BFF适合特定客户端定制聚合
4. **主动健康检查 vs 被动:** 主动检查更及时但增加后端负载，被动检查零额外开销但发现慢
