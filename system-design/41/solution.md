# 41. 设计分布式会话/Session存储 (Design Distributed Session Store)

## 题目

设计一个分布式会话存储系统，用于在微服务架构中管理用户会话状态。系统应支持高并发读写、会话过期、跨数据中心复制，并能处理节点故障。

## 需求澄清

### 功能性需求

1. **创建会话 (Create Session)**: 用户登录后创建新的 session，返回 session_id
2. **读取会话 (Read Session)**: 通过 session_id 读取会话数据
3. **更新会话 (Update Session)**: 更新会话中的属性（如添加购物车项、更新用户偏好）
4. **删除/销毁会话 (Delete Session)**: 用户登出时销毁 session
5. **会话过期 (Session Expiry)**: 支持 TTL（Time-To-Live），自动清理过期会话
6. **会话续期 (Session Renewal)**: 用户活跃时自动延长过期时间（sliding expiration）
7. **批量操作**: 支持按用户维度批量查询/删除会话

### 非功能性需求

1. **高可用 (High Availability)**: 99.99% 可用性，单节点故障不影响服务
2. **低延迟 (Low Latency)**: 读 P99 < 5ms，写 P99 < 10ms
3. **高并发 (High Throughput)**: 支持 100K+ QPS 读写
4. **数据一致性**: 会话数据需要强一致性（用户不能看到过期/不一致的会话）
5. **可扩展性 (Scalability)**: 水平扩展，支持千万级并发用户
6. **持久化 (Durability)**: 会话数据不因服务器重启而丢失（可选，视场景而定）
7. **安全性**: session_id 不可猜测，支持签名/加密

### 容量估算

假设系统有 **1 亿日活用户 (DAU)**：

```
平均每个用户 1 个活跃 session
峰值 QPS = DAU * 请求次数 / 秒数
假设每个用户每分钟 1 次 session 操作
读 QPS = 1亿 / 60 ≈ 1.67M QPS（峰值 2x = 3.3M QPS）
写 QPS ≈ 读的 20% ≈ 330K QPS（峰值 660K QPS）

平均 session 大小 = 2KB（JSON 序列化后）
存储总量 = 1亿 * 2KB = 200GB

Session TTL = 30 分钟（非活跃过期）
如果用户一直活跃，最长 24 小时绝对过期

带宽估算：
出站带宽 = 读 QPS * 2KB = 3.3M * 2KB ≈ 6.6 GB/s
入站带宽 = 写 QPS * 2KB = 660K * 2KB ≈ 1.3 GB/s
```

## API设计

### RESTful API（通过 API Gateway 暴露）

```
POST   /api/v1/sessions                   创建会话
GET    /api/v1/sessions/{session_id}      读取会话
PUT    /api/v1/sessions/{session_id}      更新会话
DELETE /api/v1/sessions/{session_id}      删除会话
POST   /api/v1/sessions/{session_id}/renew 续期会话
DELETE /api/v1/users/{user_id}/sessions   按用户登出所有会话
```

### gRPC API（内部服务间调用）

```protobuf
service SessionService {
  rpc CreateSession(CreateSessionRequest) returns (CreateSessionResponse);
  rpc GetSession(GetSessionRequest) returns (GetSessionResponse);
  rpc UpdateSession(UpdateSessionRequest) returns (UpdateSessionResponse);
  rpc DeleteSession(DeleteSessionRequest) returns (DeleteSessionResponse);
  rpc RenewSession(RenewSessionRequest) returns (RenewSessionResponse);
  rpc RevokeUserSessions(RevokeUserSessionsRequest) returns (RevokeUserSessionsResponse);
}

message CreateSessionRequest {
  string user_id = 1;
  map<string, string> attributes = 2;
  int32 ttl_seconds = 3;              // 默认 1800 (30分钟)
  int32 absolute_ttl_seconds = 4;     // 绝对过期，默认 86400 (24小时)
  string client_ip = 5;
  string user_agent = 6;
}

message CreateSessionResponse {
  string session_id = 1;
  int64 created_at = 2;
  int64 expires_at = 3;
}

message GetSessionRequest {
  string session_id = 1;
}

message GetSessionResponse {
  string session_id = 1;
  string user_id = 2;
  map<string, string> attributes = 3;
  int64 created_at = 4;
  int64 last_accessed_at = 5;
  int64 expires_at = 6;
}

message RenewSessionRequest {
  string session_id = 1;
}

message RevokeUserSessionsRequest {
  string user_id = 1;
}
```

### Session ID 生成方案

```python
import hashlib
import os
import time
import base64

def generate_session_id(user_id: str) -> str:
    """
    生成安全的 Session ID
    
    组成: timestamp(8字节) + random(16字节) + hash(timestamp + user_id + random)
    总共约 64 字节，Base64 编码后约 86 字符
    """
    timestamp = int(time.time() * 1000).to_bytes(8, 'big')
    random_bytes = os.urandom(16)
    
    # 带上 user_id 的签名，防止伪造和碰撞
    h = hashlib.sha256()
    h.update(timestamp)
    h.update(user_id.encode('utf-8'))
    h.update(random_bytes)
    
    combined = timestamp + random_bytes + h.digest()[:16]
    return base64.urlsafe_b64encode(combined).decode('utf-8').rstrip('=')
```

**为什么不直接用 UUID？**

| 方案 | 优点 | 缺点 |
|------|------|------|
| UUID v4 | 简单、标准 | 无内置防伪造，无时间信息 |
| 自签名 ID | 防伪造，带时间戳可排序 | 略长，需要自定义实现 |
| JWT | 无状态，自带信息 | Session 数据大时不适用 |

会话存储需要服务端状态，所以选择自签名 ID 方案。

## 数据模型

### Redis 数据模型（核心存储）

```
Key 设计:
  session:{session_id}                    -> Hash {user_id, created_at, last_accessed_at, ...}
  session:{session_id}:attrs              -> Hash {key1: val1, key2: val2, ...}
  user_sessions:{user_id}                 -> Set {session_id1, session_id2, ...}
  session_expiry_index                    -> Sorted Set {score=expires_at, member=session_id}
```

### Redis 具体存储结构

```
# Session 元数据 (Hash)
HSET session:aBc123... user_id "user_456"
HSET session:aBc123... created_at "1690000000"
HSET session:aBc123... last_accessed_at "1690000300"
HSET session:aBc123... absolute_expires_at "1690086400"
HSET session:aBc123... client_ip "192.168.1.1"
HSET session:aBc123... user_agent "Mozilla/5.0..."
EXPIRE session:aBc123... 1800

# Session 属性 (Hash)
HSET session:aBc123...:attrs cart_id "cart_789"
HSET session:aBc123...:attrs preferred_lang "zh-CN"
EXPIRE session:aBc123...:attrs 1800

# 用户会话索引 (Set)
SADD user_sessions:user_456 "aBc123..."
EXPIRE user_sessions:user_456 86400
```

### 为什么选择 Hash 而非 String/JSON？

| 存储方式 | 优点 | 缺点 |
|----------|------|------|
| String (JSON) | 简单，一次读写 | 不能部分更新，序列化开销 |
| Hash | 部分更新（HINCRBY etc.），内存优化 | 字段名有开销 |
| Hash per attribute | 极灵活的 TTL 管理 | 多次网络往返 |

**选型**: Hash + 分离 attributes 的 Hash，兼顾灵活性与性能。

### 如果用 MySQL（冷存储备份）

```sql
CREATE TABLE sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    attributes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    absolute_expires_at TIMESTAMP NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB
PARTITION BY RANGE (UNIX_TIMESTAMP(expires_at)) (
    PARTITION p0 VALUES LESS THAN (UNIX_TIMESTAMP('2024-01-01')),
    PARTITION p1 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    ...
);
```

## 高层次架构

```
                          ┌──────────────┐
                          │   Client     │
                          └──────┬───────┘
                                 │ HTTPS
                          ┌──────▼───────┐
                          │ API Gateway  │ (Rate Limiting, Auth)
                          └──────┬───────┘
                                 │ gRPC/HTTP
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
              │ Session   │ │ Auth  │ │ User      │
              │ Service   │ │ Svc   │ │ Profile   │
              │ (Stateless)│ │       │ │ Svc       │
              └─────┬─────┘ └───────┘ └───────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
   ┌─────▼─────┐ ┌──▼───┐ ┌───▼──────┐
   │  Redis    │ │ Redis│ │  Redis   │
   │  Cluster  │ │ Proxy│ │ Sentinel │
   │  (Primary)│ │(Sidecar)│(HA Mgmt) │
   └─────┬─────┘ └──────┘ └─────┬────┘
         │                      │
         │ Async Replication (AOF)
         │                      │
   ┌─────▼──────────────────────▼──┐
   │     Redis Cluster (Replica)   │
   │     (跨 DC 同步)               │
   └───────────────────────────────┘
         │
         │ 定期批量持久化
         │
   ┌─────▼─────┐
   │  MySQL /  │  (冷存储，用于审计/恢复)
   │  S3       │
   └───────────┘
```

### 架构设计要点

| 组件 | 技术选型 | 原因 |
|------|---------|------|
| 核心存储 | Redis Cluster | 低延迟、丰富数据结构、内置 TTL |
| 高可用 | Redis Sentinel + Cluster | 自动故障转移 |
| 持久化 | AOF everysec + RDB | 平衡性能与数据安全 |
| 冷存储 | MySQL 分区表 / S3 | 审计、长期存储 |
| 服务层 | 无状态 Go/Rust 服务 | 高性能、低 GC |
| 一致性哈希 | 服务端路由 | 确定性的节点路由 |

### 数据流

```
写入流程:
1. Client -> API Gateway (JWT 验证)
2. API Gateway -> Session Service (gRPC)
3. Session Service 生成 session_id
4. 计算哈希 -> 确定 Redis Cluster 分片
5. MULTI/EXEC 事务写入:
   - HSET session:{id} metadata
   - HSET session:{id}:attrs attributes
   - SADD user_sessions:{user_id} {session_id}
   - EXPIRE 设置 TTL
6. 返回 session_id

读取流程:
1. Client 发送 session_id (Cookie/Header)
2. Session Service 计算哈希 -> Redis 分片
3. HGETALL session:{id} 获取元数据
4. 检查是否过期 (expires_at vs now)
5. 如果未过期且启用了 sliding expiration:
   - 更新 last_accessed_at
   - 延后 expires_at (TTL 刷新)
6. HGETALL session:{id}:attrs 获取属性
7. 返回完整 session 数据
```

## 核心深入

### 方案对比：存储选型

#### 方案A: 粘性会话 (Sticky Session) + 本地缓存

```
负载均衡器根据 session_id/cookie 绑定到特定服务器
服务器内存中存储 session
```

**优点**: 极低延迟（内存读取）
**缺点**:
- 服务器宕机会话丢失
- 扩缩容时重新分配导致会话失效
- 负载不均

**不推荐**，除非对一致性要求极低。

#### 方案B: 集中式 Redis（单集群）

```
所有会话存储在共享 Redis 集群
所有服务实例无差别访问
```

**优点**: 无状态服务，易于扩展
**缺点**: Redis 成为单点/热点

#### 方案C: 分布式 Redis Cluster + 客户端分片（推荐）

```
使用 Redis Cluster 的原生分片 (16384 slots)
Session Service 使用 CRC16(session_id) % 16384 确定 slot
每个 slot 分配到一个 master + N replicas
```

**优点**: 水平扩展、自动故障转移、无单点
**缺点**: 跨 slot 操作受限（批量操作需要精心设计）

### 一致性模型

| 场景 | 一致性要求 | 实现方式 |
|------|-----------|---------|
| 读自己的 session | 强一致性 | 读写都路由到同一 master |
| 跨设备 session 同步 | 最终一致性 | 异步复制到 replicas（< 100ms） |
| 用户登出所有设备 | 最终一致性 | 标记删除，延迟清除 |
| Session 续期 | 写后读一致 | WAIT 命令等待至少 1 个 replica 确认 |

### 过期策略 (Expiration Strategies)

#### 惰性过期 + 定期清理 (Redis 默认)

```python
# Redis 内置方式
EXPIRE session:abc123 1800  # 30分钟后过期

# 读取时检查
def get_session(session_id):
    session = redis.hgetall(f"session:{session_id}")
    if not session:
        return None  # 已过期/不存在

    # Sliding expiration: 续期
    if should_renew(session):
        redis.expire(f"session:{session_id}", 1800)
        redis.hset(f"session:{session_id}", "last_accessed_at", now())

    return session
```

#### 绝对过期 + 滑动过期

```python
class SessionManager:
    SLIDING_TTL = 1800        # 30分钟不活跃后过期
    ABSOLUTE_TTL = 86400      # 24小时后无论如何过期

    def create_session(self, user_id, attrs):
        now = time.time()
        session_id = generate_session_id(user_id)
        pipe = redis.pipeline()
        pipe.hset(f"session:{session_id}", mapping={
            "user_id": user_id,
            "created_at": now,
            "last_accessed_at": now,
            "expires_at": now + self.SLIDING_TTL,
            "absolute_expires_at": now + self.ABSOLUTE_TTL,
        })
        pipe.hset(f"session:{session_id}:attrs", mapping=attrs)
        pipe.expire(f"session:{session_id}", self.ABSOLUTE_TTL)
        pipe.expire(f"session:{session_id}:attrs", self.ABSOLUTE_TTL)
        pipe.sadd(f"user_sessions:{user_id}", session_id)
        pipe.expire(f"user_sessions:{user_id}", self.ABSOLUTE_TTL)
        pipe.execute()
        return session_id

    def renew_session(self, session_id):
        """滑动续期：只在离过期还有一半时间以内时续期"""
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local sliding_ttl = tonumber(ARGV[2])
        local absolute_expires = tonumber(ARGV[3])

        local session = redis.call('HGETALL', key)
        if #session == 0 then
            return 0  -- not found
        end

        -- 检查绝对过期
        local absolute_expires_at = nil
        for i=1,#session,2 do
            if session[i] == 'absolute_expires_at' then
                absolute_expires_at = tonumber(session[i+1])
            end
        end

        if absolute_expires_at and now >= absolute_expires_at then
            return -1  -- absolutely expired
        end

        -- 只在剩余时间 < 一半 TTL 时续期
        local ttl = redis.call('TTL', key)
        if ttl < (sliding_ttl / 2) then
            redis.call('HSET', key, 'last_accessed_at', now)
            redis.call('EXPIRE', key, sliding_ttl)
            return 1  -- renewed
        end
        return 2  -- no renewal needed
        """
        return redis.eval(lua_script, 1, f"session:{session_id}",
                          int(time.time()), self.SLIDING_TTL, self.ABSOLUTE_TTL)
```

#### 定时清理过期会话

```python
# 使用 Sorted Set 作为过期索引
# 后台任务每 60 秒运行一次

def cleanup_expired_sessions():
    now = time.time()
    # ZRANGEBYSCORE: 获取所有已过期的 session_id
    expired = redis.zrangebyscore("session_expiry_index", 0, now)

    for session_id in expired:
        # 先读用户信息再删
        user_id = redis.hget(f"session:{session_id}", "user_id")
        pipe = redis.pipeline()
        pipe.delete(f"session:{session_id}")
        pipe.delete(f"session:{session_id}:attrs")
        if user_id:
            pipe.srem(f"user_sessions:{user_id}", session_id)
        pipe.zrem("session_expiry_index", session_id)
        pipe.execute()
```

### 分片策略 (Sharding Strategy)

#### Redis Cluster 原生分片

```
CRC16(key) % 16384 = slot
slot 0-5460   -> Master 1
slot 5461-10922 -> Master 2
slot 10923-16383 -> Master 3

每个 Master 有 1-2 个 Replica
```

**Key 的设计必须考虑 slot 亲和性**:
- `user_sessions:{user_id}` 和 session keys 可能在不同 slot
- 解决方案：使用 Hash Tag `{user_id}` 确保同类数据在同一 slot

```python
# 使用 Hash Tag 确保同一用户的 key 在同一 slot
session_key = f"session:{{user_456}}:abc123"
attrs_key = f"session:{{user_456}}:abc123:attrs"
index_key = f"user_sessions:{{user_456}}"

# CRC16("user_456") 决定 slot，所有此类 key 路由到同一节点
```

### 缓存策略

```
┌─────────────────────────────────────────────────┐
│                 Session Service                  │
│  ┌─────────────┐        ┌────────────────────┐  │
│  │  L1 Cache   │  miss  │  L2: Redis Cluster │  │
│  │  (Caffeine/ │ ─────► │  (分布式缓存)       │  │
│  │  本地内存)   │        │                    │  │
│  │  TTL: 60s   │        │  TTL: 30min        │  │
│  │  Max: 10K   │        │                    │  │
│  └──────┬──────┘        └─────────┬──────────┘  │
│         │ hit                     │ miss         │
│         ▼                         ▼              │
│   返回 session              返回 401/新建        │
└─────────────────────────────────────────────────┘
```

**多级缓存的影响**:
- L1 缓存降低 Redis 压力约 80%
- 但写入时需要失效 L1 缓存（使用 Redis Pub/Sub 或本地 TTL）
- 一致性风险：极端情况下 L1 缓存可能返回过期数据（60s 窗口）
- **权衡**: 如果对一致性要求极高，不使用 L1 缓存或使用极短 TTL（1-5s）

### 安全性设计

```python
def secure_session_config():
    return {
        # session_id 不可预测性
        "session_id_entropy": 128,  # bits

        # Cookie 安全属性
        "cookie_http_only": True,   # 防止 XSS 读取
        "cookie_secure": True,      # 仅 HTTPS 传输
        "cookie_same_site": "Lax",  # 防止 CSRF

        # Token 绑定
        "bind_to_ip": False,        # 绑定 IP（移动端慎用）
        "bind_to_user_agent": True, # 绑定 User-Agent

        # 异常检测
        "max_sessions_per_user": 10,
        "suspicious_ip_change_action": "reauthenticate",
    }
```

### 监控与告警

| 指标 | 告警阈值 | 说明 |
|------|---------|------|
| Session 创建 QPS | > 2x baseline | 可能遭受攻击 |
| Session 读取延迟 P99 | > 10ms | Redis 性能问题 |
| Redis 内存使用率 | > 80% | 需要扩容或清理 |
| 过期会话比例 | > 30% | TTL 配置可能不合理 |
| Redis 主从延迟 | > 1s | 复制链路问题 |
| 会话创建失败率 | > 0.1% | 服务异常 |
| L1 缓存命中率 | < 70% | 缓存配置问题 |

## 扩展性与高可用

### 水平扩展

```
Session Service 层:
  - 无状态，通过 K8s HPA 基于 CPU/内存/QPS 自动扩缩
  - 扩散式的一致性哈希：服务实例启动时注册到服务发现

Redis Cluster 层:
  - 动态添加 Master 节点 + Reshard
  - redis-cli --cluster reshard <new-node>:6379
  - 迁移 slot 时对业务透明（ASK 重定向）
```

### 跨数据中心部署

```
                    ┌──────────────────────────┐
                    │   Global DNS (Geo-Route) │
                    └──────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │  DC-East  │   │  DC-West  │   │  DC-Asia  │
        │ (Primary  │   │ (Primary  │   │ (Primary  │
        │  for East │   │  for West │   │  for Asia │
        │  users)   │   │  users)   │   │  users)   │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │                │                │
              │  Async Replication (CRDT/Gossip)│
              └────────────────┼────────────────┘
                               │
                        Session 数据就近访问
                        用户迁移时 session 在主 DC 间同步
```

**用户地域路由策略**:
- 用户注册时绑定主 DC
- Session 始终在主 DC 读写（避免跨 DC 延迟）
- 用户旅行到其他区域时，通过 CDN 边缘节点加速（但不能绕过主 DC 写入）

### 灾难恢复

| 场景 | 恢复策略 | RTO | RPO |
|------|---------|-----|-----|
| 单 Redis 节点故障 | Sentinel 自动切换 Replica | < 30s | < 1s |
| 整个 Redis Cluster 故障 | 切换到备用集群 + 从 MySQL/S3 恢复冷数据 | < 5min | < 5min |
| 整个 DC 故障 | DNS 切换 + 用户路由到备用 DC | < 15min | < 5min |
| 数据误删 | AOF 文件回放恢复 | < 30min | 取决于备份频率 |

### 流量突增应对

```python
# 1. 优雅降级：连接数过高时拒绝非关键 session 创建
def create_session_with_backpressure(user_id, attrs):
    if redis_pool.available_connections < MIN_CONNECTIONS:
        if attrs.get("is_critical", False):
            # 关键请求排队等待
            return create_with_queue(user_id, attrs)
        else:
            raise SessionOverloaded("请稍后重试")

    return create_session(user_id, attrs)

# 2. 写缓冲：批量写入
class WriteBuffer:
    def __init__(self, flush_interval=0.1):
        self.buffer = {}
        self.flush_interval = flush_interval

    async def buffer_write(self, session_id, field, value):
        key = f"session:{session_id}"
        if key not in self.buffer:
            self.buffer[key] = {}
        self.buffer[key][field] = value

    async def flush(self):
        pipe = redis.pipeline()
        for key, fields in self.buffer.items():
            pipe.hset(key, mapping=fields)
        pipe.execute()
        self.buffer.clear()
```

### CAP 定理分析

Session 存储通常选择 **CP** 或 **AP**，具体取决于场景：

| 选择 | 适用场景 | 实现方式 |
|------|---------|---------|
| CP（一致性+分区容忍） | 金融、电商等对一致性要求高的 | Redis Cluster + WAIT 命令，写入时等待 replica 确认 |
| AP（可用性+分区容忍） | 社交、内容平台，可用性优先 | 允许短暂不一致，网络分区时继续服务 |

**推荐**: 电商/金融选 CP，社交/内容选 AP。大多数场景下，Redis Cluster 的异步复制（AP倾向）已经足够。

## 总结

分布式 Session 存储的核心设计要点：

1. **存储选型**: Redis Cluster 是最合适的选择——低延迟、丰富数据结构、原生 TTL、集群模式支持
2. **一致性模型**: 根据业务场景在 CP 和 AP 之间选择，电商/金融应在写入时使用 WAIT 命令确保 replica 确认
3. **过期策略**: 结合惰性过期 + 定期清理 + 滑动续期，使用 Sorted Set 管理过期索引
4. **分片策略**: 使用 Redis Cluster 的 Hash Slot 机制，通过 Hash Tag 确保同一用户数据共置
5. **多级缓存**: L1 本地缓存 (Caffeine) + L2 Redis Cluster，注意缓存一致性
6. **高可用**: Sentinel 自动故障转移 + 跨 DC 异步复制 + 冷存储备份
7. **安全**: session_id 带签名防伪造，Cookie 设置 HttpOnly/Secure/SameSite
8. **监控**: 关注延迟 P99、内存使用率、主从复制延迟、过期比例

面试中面试官可能会追问 Redis Cluster resharding 期间的一致性保证、跨 DC session 迁移的具体协议、以及如何使用 Lua 脚本实现原子操作。
