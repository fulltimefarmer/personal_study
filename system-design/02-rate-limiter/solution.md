# 题目：Design a Rate Limiter

## 需求澄清（Requirement Clarification）

### 功能需求
1. 限制每个用户/API Key 在单位时间内的请求次数。
2. 支持多种限流粒度：每秒、每分钟、每小时、每天。
3. 超出限制时返回 HTTP 429 Too Many Requests，并附带 `Retry-After` 头信息。
4. 支持对不同 API 端点设置不同的限流规则。
5. 提供管理接口，动态调整限流参数（无需重启服务）。
6. 限流信息写入监控系统，用于告警和分析。
7. 支持白名单（VIP 用户不受限流约束）。

### 非功能需求
- **低延迟**：限流判断必须在 1ms 内完成，不能成为瓶颈。
- **高可用**：限流服务挂掉不应影响整个系统（fail-open 或降级）。
- **扩展性**：支持百万级 QPS 的流量。
- **分布式一致性**：在分布式环境中限流计数需要全局一致（或允许近似一致）。

### 容量估算
- **日请求量**：假设系统总 QPS 峰值为 1M，即每天约 86B 次请求。
- **限流计数器**：每天有 ~100M 个独立的 API Key，每个 Key 需存储多个时间窗口的计数。每个 Key 约占 100 Bytes，总内存 ≈ 10GB（可放入 Redis 集群）。
- **带宽**：每次请求调用限流服务，需 1M QPS × 约 200B/请求 ≈ 200MB/s。

---

## 系统接口（API Design）

### 1. 限流检查（内部调用/中间件）

限流通常在 API Gateway 或中间件层完成，不直接暴露对外的 API，而是作为内部调用：

```go
// 内部中间件接口
func CheckRateLimit(ctx context.Context, key string, limit int, window time.Duration) (allowed bool, remaining int, resetAt time.Time, err error)
```

返回信息设置到 HTTP Response Header：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1627654321
```

### 2. 管理接口（Admin API）

```
# 获取限流规则
GET /admin/rate-limit/rules

Response 200:
{
  "rules": [
    {
      "id": "rule_001",
      "api_path": "/api/v1/urls",
      "method": "POST",
      "limit": 100,
      "window": "1m",
      "enabled": true
    }
  ]
}

# 创建/更新限流规则
PUT /admin/rate-limit/rules/{id}
Request:
{
  "api_path": "/api/v1/urls",
  "method": "POST",
  "limit": 200,
  "window": "1m"
}

Response 200: { "status": "ok" }

# 添加白名单
PUT /admin/rate-limit/whitelist
Request: { "key": "user_vip_123" }
Response 200: { "status": "ok" }
```

### 3. 限流事件写入

超出限制时，向 Kafka 发送限流事件用于监控：

```
Topic: rate_limit_events
Message: {
  "key": "user_123",
  "api": "/api/v1/urls",
  "timestamp": "...",
  "reason": "exceeded_limit"
}
```

---

## 数据模型（Data Model）

### Redis 计数器结构

限流计数器存储在 Redis 中，数据结构取决于限流算法：

#### 固定窗口
```
Key: ratelimit:{api_key}:{window_start_ts}
Value: 计数器（整数）
TTL: 窗口大小的 2 倍
```

#### 滑动窗口
```
Key: ratelimit:{api_key}
Type: Sorted Set (ZSET)
Member: 每次请求的唯一 ID（如 UUID 或纳秒时间戳 + 随机数）
Score: 请求的 Unix 时间戳（毫秒）
```

#### 令牌桶
```
Key: ratelimit:{api_key}:tokens
Value: 当前令牌数（整数）
Key: ratelimit:{api_key}:last_refill
Value: 上次补充令牌的时间戳
```

### 规则配置表（MySQL）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | BIGINT (PK) | 规则 ID |
| api_path | VARCHAR(256) | API 路径模式 |
| method | VARCHAR(10) | HTTP 方法 |
| limit_amount | INT | 在时间窗口内的最大请求数 |
| window_seconds | INT | 时间窗口（秒） |
| enabled | TINYINT | 启用状态 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

规则表数据量小（几百条），缓存到内存中，通过定时轮询或发布订阅刷新。

---

## 架构设计（High-Level Design）

### 架构图（ASCII）

```
                   ┌──────────────────────────────────┐
                   │           Internet                │
                   └──────────────┬───────────────────┘
                                  │
                   ┌──────────────▼───────────────────┐
                   │         Load Balancer            │
                   └──────────────┬───────────────────┘
                                  │
                   ┌──────────────▼───────────────────┐
                   │  API Gateway / Reverse Proxy     │
                   │  (Nginx / Kong / APISIX)         │
                   │  ┌────────────────────────────┐  │
                   │  │   Rate Limiter Middleware   │  │
                   │  └────────────────────────────┘  │
                   └──────────────┬───────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
           ┌────────▼──┐  ┌──────▼──────┐  ┌───▼──────────┐
           │  Redis     │  │  API Server │  │  Rate Limit   │
           │  Cluster   │  │  (Business) │  │  Admin API    │
           └────────────┘  └────────────┘  └───┬───────────┘
                                               │
                                        ┌──────▼──────┐
                                        │    MySQL     │
                                        │ (Rule Store) │
                                        └─────────────┘
```

### 组件职责

| 组件 | 职责 |
|------|------|
| **API Gateway** | 统一流量入口，在网关层执行限流中间件，拦截超限请求 |
| **Rate Limiter Middleware** | 核心逻辑：解析 API Key → 查询 Redis 计数 → 判断是否超限 → 拒绝/放行 |
| **Redis Cluster** | 分布式计数器存储，支持原子操作（INCR、ZADD、Lua 脚本） |
| **Rate Limit Admin API** | 管理限流规则和白名单，CRUD 操作写入 MySQL 并广播更新 |
| **MySQL** | 持久化限流规则配置、白名单数据 |
| **Kafka** | 异步接收限流事件，批量写入监控大盘、触发告警 |
| **Prometheus + Grafana** | 监控限流命中率、拒绝率、各 API Key 实时 QPS |

---

## 深入探讨（Deep Dive）

### 1. 限流算法对比

#### a) 固定窗口（Fixed Window）

**原理**：将时间线划分为固定窗口（如每分钟），每个窗口内维护一个计数器。新请求到来时 INCR 计数器，超过阈值即拒绝。

```
时间轴:  |--- 窗口1 ---|--- 窗口2 ---|--- 窗口3 ---|
计数器:      0→50          0→100         0→30
```

- **优点**：实现极其简单（Redis INCR + EXPIRE），内存占用低。
- **缺点**：**边界突发问题**。在第 1 个窗口末尾和第 2 个窗口开头瞬间发送 2 倍限额的流量，实际 QPS 可突破限制。
- **适用**：对精度要求不高的场景，如论坛发帖频率限制。

#### b) 滑动窗口（Sliding Window）

**原理**：维护一个按时间排序的请求队列（ZSET），每次请求清理窗口外的旧记录，统计窗口内记录数。

```
ZSET: score = timestamp_ms
      member = unique_request_id

判断流程：
  1. ZREMRANGEBYSCORE key 0 (now - window_ms)   // 移除过期记录
  2. ZCARD key                                    // 统计当前记录数
  3. 如果 < limit → ZADD key now request_id → 放行
  4. 如果 ≥ limit → 拒绝
```

- **优点**：精确到毫秒级别，无边界突发问题。
- **缺点**：每条请求写入一个 ZSET 成员，内存占用较高（且无法自动过期整个 ZSET，需要定期清理）。
- **优化**：使用 Hash + List 替代 ZSET；或采用**滑动窗口日志**的近似实现：将窗口分为多个小格子，用 `INCR` 统计小格子计数，滑动求和。

**推荐方案：滑动窗口（计数器优化版）**

将时间窗口划分为 N 个小格（如 1 分钟窗口 → 60 个 1 秒小格），使用 Redis Hash：
```
Key: ratelimit:{api_key}
Hash Field: 时间戳取整到秒
Hash Value: 该秒内的请求计数
```
判断时计算过去 N 秒内所有 field 的 value 之和，与 limit 比较。内存更节省，精度损失可接受（1 秒粒度）。

#### c) 令牌桶（Token Bucket）

**原理**：桶以固定速率产生令牌（capacity 为桶最大容量）。请求到达时需消耗一个令牌，有令牌则放行，无令牌则拒绝。

```
每过 1/rate 秒 → 补充 1 个令牌（不超过 capacity）

请求到达 → 当前令牌数 ≥ 1 → 消耗 1 个令牌 → 放行
                              → if 0 → 拒绝
```

- **优点**：允许一定的突发流量（桶内可累积令牌），平滑限流同时兼顾灵活性。
- **缺点**：需要记录上次补充时间，实现较复杂。
- **适用**：允许短期内突发、但长期平均速率受限的场景（如 API 调用）。

**Redis Lua 脚本实现令牌桶**：
```lua
-- KEYS[1]: 令牌计数 key
-- KEYS[2]: 上次补充时间 key
-- ARGV[1]: 容量 capacity
-- ARGV[2]: 补充速率 rate (tokens/sec)
-- ARGV[3]: 当前时间 now (ms)

local tokens_key = KEYS[1]
local timestamp_key = KEYS[2]
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local fill_time = tonumber(redis.call('get', timestamp_key)) or now
local tokens = tonumber(redis.call('get', tokens_key)) or capacity

local elapsed = math.max(0, now - fill_time)
local new_tokens = math.min(capacity, tokens + elapsed * rate / 1000)

if new_tokens < 1 then
    redis.call('set', tokens_key, new_tokens)
    redis.call('set', timestamp_key, now)
    return 0  -- 拒绝
else
    redis.call('set', tokens_key, new_tokens - 1)
    redis.call('set', timestamp_key, now)
    return 1  -- 放行
end
```

#### d) 漏桶（Leaky Bucket）

**原理**：请求进入队列（桶），以恒定速率从队列取出并处理。桶满时新请求被拒绝。

- **优点**：绝对平滑输出速率，适合流量整型。
- **缺点**：无法处理突发流量，即使服务器有余力也会被限速。
- **适用**：对输出速率有严格要求的场景（如发短信）。

### 2. 分布式限流实现

#### Redis Cluster 方案

| 策略 | 描述 | 一致性 | 性能 |
|------|------|--------|------|
| **单节点 Redis** | 所有计数集中到同一 Redis 实例 | 强一致 | 受限于单实例 QPS（~100K） |
| **Redis Cluster 分区** | 按 API Key 哈希路由到固定分片 | 强一致（同 Key 同分片） | 无上限水平扩展 |
| **Redis Cluster + 异步复制** | 主从异步复制，读取可能读到旧值 | 最终一致 | 高吞吐 |

**推荐**：Redis Cluster，按 `api_key` 的 hash 路由到固定 slot，保证每个 key 的计数原子性。Lua 脚本在 Redis 内部原子执行，避免应用层的 check-and-set 竞态条件。

#### 本地限流 + 集中式限流（双层限流）

- **第一层（本地）**：在 API Gateway 内存中维护粗粒度的本地限流器，仅需极低延迟。
- **第二层（全局）**：定期与 Redis 同步计数，确保全局精确控制。
- **优点**：将限流延迟降到微秒级；Redis 不可用时本地限流器仍可工作（降级模式）。

---

## 扩展与高可用

### 水平扩展
- **API Gateway**：无状态，增加实例即可扩展。K8s 水平自动伸缩。
- **Redis Cluster**：增加节点后通过 reshard 迁移 slot 实现扩容。
- **限流规则同步**：规则更新通过 Redis Pub/Sub 或消息队列广播给所有 Gateway 实例，实时生效。

### 故障转移（Failover）
- **Redis 高可用**：Sentinel 模式监控主节点，主节点宕机后自动提升从节点。
- **降级策略**：
  - **Fail-open**：Redis 不可用时，放开所有请求（防止限流器引发大面积故障）。
  - **Fail-closed**：Redis 不可用时，拒绝所有请求（安全优先）。
  - **推荐**：混合策略 —— 核心支付接口 fail-closed，一般查询接口 fail-open。
- **Circuit Breaker**：限流中间件集成熔断器，Redis 持续失败时自动切换为降级模式。

### 数据备份与恢复
- 限流计数器是瞬态数据，无需持久化备份。Redis AOF 持久化可选开启以防重启清空。
- **规则配置**：MySQL 主从复制 + 定期备份。
- **恢复流程**：Redis Cluster 重启后从 AOF 恢复；规则表从 MySQL 恢复并预热到内存缓存。

---

## 总结

### 关键设计决策回顾
1. **算法选型**：关键 API 使用**滑动窗口**保证精确限流；允许突发的场景使用**令牌桶**；内部调用用简单的**固定窗口**降低开销。
2. **存储选型**：Redis 作为计数器存储（内存 + 原子操作 + Lua）。
3. **分布式一致性**：按 API Key 哈希路由到 Redis Cluster 固定 Slot，保证同 Key 的原子性。
4. **降级策略**：双层限流（本地 + 远程），远程不可用时自动降级到本地限流。
5. **配置热更新**：规则配置通过 Pub/Sub 推送，无需重启网关。

### 可能的改进方向
- 结合机器学习预测流量模式，自适应调整限流阈值。
- 分布式场景下使用 **Raft/Paxos** 协议实现无 Redis 的强一致分布式限流。
- 引入**配额系统**：用户可购买更高配额，限流与计费集成。
- 边缘限流：用 WebAssembly 插件在 Envoy 网关层做原生限流，减少网络跳转。
- 限流层级细化：全局限流 → 服务级限流 → 用户级限流 → API 级限流，多层级联动。
