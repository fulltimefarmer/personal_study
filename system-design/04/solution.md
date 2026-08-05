# 04. 设计限流器 (Design Rate Limiter)

## 题目

设计一个限流器（Rate Limiter），用于控制客户端对 API 的访问频率，防止滥用和资源过载。限流器可以部署为独立服务或集成到 API Gateway 中。

---

## 需求澄清

### 功能性需求

1. **精确限流**：限制单个用户/IP/API Key 在一定时间窗口内的请求次数
2. **多种限流维度**：支持按用户、IP、API Key、API 端点等维度限流
3. **多种限流规则**：支持不同时间窗口和不同阈值的规则
4. **分布式限流**：跨多台服务器共享限流状态
5. **返回限流信息**：返回剩余请求次数、重置时间、是否被限流
6. **限流结果处理**：被限流时返回 429 Too Many Requests + 重试提示
7. **动态规则配置**：支持热更新限流规则，无需重启
8. **限流日志与监控**：记录限流事件，用于分析和告警

### 非功能性需求

1. **低延迟**：限流判断延迟 < 1ms (P99 < 5ms)
2. **高可用**：限流器故障不应阻断正常请求（故障开放 / fail-open）
3. **高并发**：支持百万级 QPS
4. **准确性**：在分布式环境下误差 < 1%
5. **可扩展**：支持添加新的限流算法和策略
6. **低内存占用**：高效存储计数器，支持海量用户

### 容量估算

**假设条件：**
- 系统总 QPS: 1M
- 需要限流的用户数: 1 亿
- 每个用户需要追踪的计数器数量: 5 个（不同时间窗口）
- 平均限流窗口: 1 分钟

**存储估算：**
- 每个计数器: 约 50 bytes（Hash数据结构的开销 + 计数 + 时间戳）
- 总存储 = 1 亿 × 5 × 50 bytes ≈ **25 GB**
- Redis 实际内存（含开销）: ~35 GB（可接受，单 Redis 集群即可）

**延迟估算：**
- 限流检查需要在每次请求时进行
- 1M QPS → 每个请求 < 1μs? 不可能
- 实际方案: 多实例 + Redis Cluster，每实例 ~10K QPS，Redis 延迟 ~0.5ms

---

## API 设计

### 限流器服务接口

```
1. 检查请求是否被限流
POST /ratelimit/v1/check
Content-Type: application/json

Request:
{
  "key": "user:12345:api:send_message",   // 限流键
  "resource": "api:send_message",          // 资源标识
  "timestamp": 1704067200000               // 请求的时间戳（毫秒）
}

Response: 200 OK
{
  "allowed": true,
  "remaining": 89,                         // 剩余请求次数
  "limit": 100,                            // 限流阈值
  "reset_time": 1704067260000,             // 窗口重置的 Unix 毫秒时间戳
  "retry_after_ms": null                   // 如果被限流，等待多少毫秒后重试
}

--- 如果被限流 ---

Response: 200 OK
{
  "allowed": false,
  "remaining": 0,
  "limit": 100,
  "reset_time": 1704067260000,
  "retry_after_ms": 58423
}
```

### API Gateway 集成方式

```
# API Gateway 中间件伪代码

def rate_limit_middleware(request):
    # 1. 构造限流键
    key = build_rate_limit_key(request)

    # 2. 获取适用规则
    rules = get_rate_limit_rules(request.api_endpoint)

    # 3. 对每条规则进行检查
    for rule in rules:
        result = rate_limiter.check(
            key=f"{key}:{rule.window_type}",
            threshold=rule.threshold,
            window=rule.window_seconds
        )
        if not result.allowed:
            # 设置响应头
            response = Response(status=429)
            response.headers["X-RateLimit-Limit"] = str(rule.threshold)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(result.reset_time)
            response.headers["Retry-After"] = str(result.retry_after_seconds)
            response.body = {
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Try again in {result.retry_after_seconds}s"
            }
            return response

    # 4. 设置正常响应头
    response = process_request(request)
    response.headers["X-RateLimit-Limit"] = str(rule.threshold)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_time)
    return response
```

### 管理 API（可选）

```
1. 创建限流规则
POST /ratelimit/v1/rules
Authorization: Bearer <admin_token>

Request:
{
  "name": "per_user_send_message",
  "resource": "api:send_message",
  "key_pattern": "user:{user_id}:api:send_message",
  "threshold": 100,
  "window_seconds": 60,
  "algorithm": "sliding_window_log"
}

Response: 201 Created

2. 查询限流规则
GET /ratelimit/v1/rules

3. 查询当前限流状态
GET /ratelimit/v1/status?key=user:12345:api:send_message

4. 重置限流计数器
POST /ratelimit/v1/reset
{
  "key": "user:12345:*"   // 支持通配符
}
```

---

## 数据模型

### Redis 数据结构设计（按算法）

```
# 算法1: 固定窗口计数器 (Fixed Window Counter)
Key:     ratelimit:{key}:{window}:{timestamp_bucket}
Type:    String
Value:   计数器值
TTL:     window_seconds * 2
示例:    ratelimit:user:123:send_msg:minute:17100000
         SET ratelimit:... 1 EX 120 NX   # 原子创建
         INCR ratelimit:...               # 原子递增

# 算法2: 滑动窗口日志 (Sliding Window Log)
Key:     ratelimit:log:{key}
Type:    Sorted Set
Score:   请求时间戳（毫秒）
Member:  请求唯一ID (UUID/纳秒时间戳 + 随机数)
操作:    
  ZADD ratelimit:log:user:123 1704067200123 "uuid-xxx"
  ZREMRANGEBYSCORE ratelimit:log:user:123 0 {now - window_ms}
  ZCARD ratelimit:log:user:123
  EXPIRE ratelimit:log:user:123 window_seconds * 2

# 算法3: 滑动窗口计数器 (Sliding Window Counter)【推荐】
Key:     ratelimit:swc:{key}
Type:    Hash
Fields:  
  - prev_count:  前一个窗口的计数值
  - curr_count:  当前窗口的计数值
  - prev_window: 前一个窗口的起始时间戳
  - curr_window: 当前窗口的起始时间戳
TTL:     window_seconds * 3

# 算法4: Token Bucket (令牌桶)
Key:     ratelimit:token:{key}
Type:    Hash
Fields:
  - tokens:       当前可用令牌数 (double)
  - last_refill:  上次补充时间戳（毫秒）
  - capacity:     桶容量
  - rate:         令牌生成速率 (tokens/sec)
TTL:      bucket_idle_timeout
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────┐
                              │              Clients                 │
                              └──────────────────┬───────────────────┘
                                                 │
                              ┌──────────────────▼───────────────────┐
                              │          API Gateway / LB            │
                              │     (Nginx / Kong / Envoy / 自研)     │
                              │                                      │
                              │  ┌────────────────────────────────┐  │
                              │  │   Rate Limiter Middleware       │  │
                              │  │   (本地预检 + 远程调用)          │  │
                              │  └────────────┬───────────────────┘  │
                              └───────────────┼──────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
          ┌─────────▼──────────┐    ┌─────────▼──────────┐    ┌─────────▼──────────┐
          │ Rate Limiter Svc   │    │ Rate Limiter Svc   │    │ Rate Limiter Svc   │
          │ Instance 1         │    │ Instance 2         │    │ Instance N         │
          │                    │    │                    │    │                    │
          │ ┌────────────────┐ │    │ ┌────────────────┐ │    │ ┌────────────────┐ │
          │ │ 本地缓存        │ │    │ │ 本地缓存        │ │    │ │ 本地缓存        │ │
          │ │ (Caffeine)     │ │    │ │ (Caffeine)     │ │    │ │ (Caffeine)     │ │
          │ │ 同步间隔:      │ │    │ │ 同步间隔:      │ │    │ │ 同步间隔:      │ │
          │ │ 100ms-1s       │ │    │ │ 100ms-1s       │ │    │ │ 100ms-1s       │ │
          │ └────────────────┘ │    │ └────────────────┘ │    │ └────────────────┘ │
          └─────────┬──────────┘    └─────────┬──────────┘    └─────────┬──────────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                              ┌───────────────▼─────────────────────────┐
                              │            Redis Cluster                │
                              │          (Sentinel / Redis Cluster)     │
                              │                                        │
                              │  ┌──────────┐  ┌──────────┐            │
                              │  │ Master-1 │  │ Master-2 │  ...       │
                              │  │ Slave-1  │  │ Slave-2  │            │
                              │  └──────────┘  └──────────┘            │
                              └────────────────────────────────────────┘
                                              │
                              ┌───────────────▼─────────────────────────┐
                              │          配置与监控中心                   │
                              │  ┌──────────────────────────────────┐   │
                              │  │  Rule Config Store (etcd/Config) │   │
                              │  │  Metrics (Prometheus + Grafana)  │   │
                              │  │  Alerting (PagerDuty/Slack)      │   │
                              │  └──────────────────────────────────┘   │
                              └────────────────────────────────────────┘
```

---

## 核心深入

### 限流算法对比

#### 1. Token Bucket (令牌桶)

```
原理:
  ┌─────────────┐
  │  令牌生成器   │──Rate: r tokens/sec──▶ ┌───────────┐
  │ (refiller)  │                        │  Bucket   │
  └─────────────┘                        │ capacity: │
                                         │   b 令牌   │
                                         └─────┬─────┘
                                               │
                                         每个请求需要 1 个令牌
                                         有令牌 → 放行
                                         无令牌 → 限流

特点:
  - 允许突发流量 (Burst): 桶容量 b 决定了最大突发量
  - 平滑限流: 长期平均速率 = r
  - 令牌桶满后丢弃新令牌（不能超过容量）

参数:
  - rate (r): 令牌生成速率
  - capacity (b): 桶最大容量
  - burst_size = b - 1 (最大突发请求数)
```

```python
# Token Bucket Lua Script (Redis)
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])        -- tokens per second
local capacity = tonumber(ARGV[2])     -- max tokens
local requested = tonumber(ARGV[3])    -- tokens requested (usually 1)
local now = tonumber(ARGV[4])         -- current time in ms

-- Get current state
local tokens = tonumber(redis.call('HGET', key, 'tokens')) or capacity
local last_refill = tonumber(redis.call('HGET', key, 'last_refill')) or now

-- Calculate tokens to add since last refill
local elapsed_ms = math.max(0, now - last_refill)
local refill_tokens = (elapsed_ms / 1000) * rate
tokens = math.min(capacity, tokens + refill_tokens)

-- Check if enough tokens
local allowed = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

-- Update state
redis.call('HSET', key, 'tokens', tokens)
redis.call('HSET', key, 'last_refill', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) * 2)

return {allowed, tokens, capacity}
"""
```

#### 2. Leaky Bucket (漏桶)

```
原理:
  ┌────────────────────────────────────┐
  │          请求流入 (不限速)            │
  │              ↓ ↓ ↓ ↓               │
  │         ┌─────────────┐            │
  │         │  漏桶 Queue   │            │
  │         │  Size: N     │ ← 溢出则丢弃  │
  │         └──────┬──────┘            │
  │                │                    │
  │                ▼                    │
  │         恒定速率流出 (r req/s)        │
  └────────────────────────────────────┘

特点:
  - 恒定速率输出 (流量整形)
  - 队列满时丢弃请求
  - 不允许突发 (没有 burst 概念)
  - 适合需要稳定输出速率的场景

Token Bucket vs Leaky Bucket:
  Token:  允许突发，适合大多数 API 限流场景
  Leaky:  平滑输出，不允许突发，适合流量整形（Traffic Shaping）
```

#### 3. Fixed Window Counter (固定窗口计数器)

```
原理:
  时间窗口: [00:00 - 00:01), [00:01 - 00:02), ...
  每个窗口独立计数器

  问题: 边界突发
  ─────────────────────────────────────
  窗口1: [0────59秒────]  窗口2: [0────59秒────]
  
  假设限制: 100 req/min
  在 00:00:59 发送 100 个请求  ✓
  在 00:01:00 发送 100 个请求  ✓
  → 2 秒内发送了 200 个请求! (实际速率是限制的 2 倍)

优点: 实现简单，内存占用低
缺点: 窗口边界突发问题
内存: O(1) per key
```

```python
# Fixed Window Counter Lua Script
FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]
local threshold = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Calculate window bucket
local window = math.floor(now / (window_seconds * 1000))
local bucket_key = key .. ':' .. window

-- Increment counter
local count = redis.call('INCR', bucket_key)
redis.call('EXPIRE', bucket_key, window_seconds * 2)

local allowed = count <= threshold and 1 or 0
local remaining = math.max(0, threshold - count)

return {allowed, remaining, threshold, (window + 1) * window_seconds * 1000}
"""
```

#### 4. Sliding Window Log (滑动窗口日志)

```
原理:
  记录每次请求的时间戳
  每次请求时清理过期日志
  统计窗口内的请求数

优点: 精确限流，无边界问题
缺点: 内存占用高，每次请求需要清理和计算
  
内存: O(count) per key (与请求数成正比)
```

```python
# Sliding Window Log Lua Script
SLIDING_WINDOW_LOG_SCRIPT = """
local key = KEYS[1]
local threshold = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window_ms)

-- Add current request
local member = now .. ':' .. ARGV[4]  -- unique member
redis.call('ZADD', key, now, member)

-- Count current window
local count = redis.call('ZCARD', key)
redis.call('EXPIRE', key, math.ceil(window_ms / 1000) * 2)

local allowed = count <= threshold and 1 or 0
local remaining = math.max(0, threshold - count)

return {allowed, remaining, threshold}
"""
```

#### 5. Sliding Window Counter (滑动窗口计数器)【推荐】

```
原理:
  结合固定窗口和滑动窗口的优点
  当前窗口的限制 = 前一个窗口的加权计数值 + 当前窗口计数值

  时间轴:
  ────────┬──────┬───────────────────────
          │      │
    prev_window  curr_window
  
  权重: prev_window 贡献 = (1 - overlap_ratio)
        curr_window 贡献 = 1.0

  公式:
  estimated_count = prev_count * (1 - overlap_ratio) + curr_count
  overlap_ratio = elapsed_in_current_window / window_size  

优点:
  - 近似精确，误差 < 1%
  - 内存占用: O(2) per key (只需保存两个窗口的计数)
  - 无窗口边界突发问题
  
缺点:
  - 是近似算法，不是严格精确
```

```python
# Sliding Window Counter Lua Script
SLIDING_WINDOW_COUNTER_SCRIPT = """
local key = KEYS[1]
local threshold = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local now = tonumber(ARGV[3])  -- milliseconds

local window_ms = window_seconds * 1000
local curr_window_start = math.floor(now / window_ms) * window_ms
local prev_window_start = curr_window_start - window_ms

-- Get current and previous window counts
local curr_count = tonumber(redis.call('HGET', key, 'curr_count')) or 0
local prev_count = tonumber(redis.call('HGET', key, 'prev_count')) or 0
local stored_curr_window = tonumber(redis.call('HGET', key, 'curr_window')) or curr_window_start

-- Check if window has advanced
if stored_curr_window < curr_window_start then
    -- Shift window: prev ← curr, curr ← 0
    prev_count = curr_count
    curr_count = 0
    redis.call('HSET', key, 'prev_count', prev_count)
    redis.call('HSET', key, 'prev_window', stored_curr_window)
    redis.call('HSET', key, 'curr_window', curr_window_start)
end

-- Calculate weighted count
local elapsed_in_window = now - curr_window_start
local overlap_ratio = elapsed_in_window / window_ms
local weighted_count = prev_count * (1 - overlap_ratio) + curr_count

-- Increment current window count
curr_count = redis.call('HINCRBY', key, 'curr_count', 1)
redis.call('HINCRBY', key, 'curr_window', 0)  -- ensure field exists

-- Update weighted count
weighted_count = prev_count * (1 - overlap_ratio) + curr_count

redis.call('EXPIRE', key, window_seconds * 3)

local allowed = weighted_count <= threshold and 1 or 0
local remaining = math.max(0, math.floor(threshold - weighted_count))
local reset_time = curr_window_start + window_ms

return {allowed, remaining, threshold, reset_time}
"""
```

```python
# Sliding Window Counter (无 Redis 依赖, 纯内存实现)
# 适合作为 API Gateway 的本地限流

import time
from collections import defaultdict
from threading import Lock

class InMemorySlidingWindowRateLimiter:
    def __init__(self):
        self._windows = {}
        self._lock = Lock()

    def is_allowed(self, key: str, threshold: int, window_seconds: int) -> bool:
        now_ms = int(time.time() * 1000)
        window_ms = window_seconds * 1000
        curr_window_start = (now_ms // window_ms) * window_ms

        with self._lock:
            state = self._windows.get(key, {
                'curr_count': 0, 'prev_count': 0, 'curr_window': curr_window_start
            })

            if state['curr_window'] < curr_window_start:
                state['prev_count'] = state['curr_count']
                state['curr_count'] = 0
                state['curr_window'] = curr_window_start

            elapsed = now_ms - curr_window_start
            weighted = state['prev_count'] * (1 - elapsed / window_ms) + state['curr_count']

            if weighted < threshold:
                state['curr_count'] += 1
                self._windows[key] = state
                return True
            return False
```

#### 算法对比总结

| 算法 | 精度 | 内存占用 | 突发支持 | Redis复杂度 | 推荐场景 |
|------|------|----------|----------|-------------|----------|
| Token Bucket | 精确 | O(1) | 可配置 burst | 中等 | **通用API限流** |
| Fixed Window | 不精确 | O(1) | 边界突发 | 低 | 不严格场景 |
| Sliding Window Log | 精确 | O(n) | 平滑 | 高 | 严格精确限流 |
| Sliding Window Counter | 近似(<1%误差) | O(1) | 平滑 | 中等 | **推荐** |
| Leaky Bucket | 精确 | O(n) | 不支持 | 高 | 流量整形 |

### 分布式限流的挑战

**问题1：时钟不同步**
```
解决方案:
  - Redis 作为单一时间源（使用 SERVER TIME）
  - Lua 脚本中使用 Redis 的 TIME 命令获取时间
  - 避免使用客户端时间戳
```

**问题2：竞争条件 (Race Condition)**
```
解决方案:
  - Redis Lua 脚本保证原子性
  - Lua 脚本在 Redis 服务端单线程执行
  - 或使用 Redis 事务 (MULTI/EXEC, 但不如 Lua 灵活)
```

**问题3：Redis 故障时策略**

```
# Fail-open vs Fail-close 策略

Fail-open (故障开放):
  - Redis 不可用时，允许所有请求通过
  - 优点: 业务可用性最高
  - 缺点: 限流失效，后端可能被冲垮
  - 适用: 限流是辅助功能，业务可用性第一

Fail-close (故障关闭):
  - Redis 不可用时，拒绝所有请求
  - 优点: 保护后端
  - 缺点: 正常用户也被拒绝
  - 适用: 后端保护是首要目标

推荐: 混合策略
  - Redis 故障 + 消息速率未超限(本地限流) → fail-open
  - Redis 故障 + 本地限流被触发 → 逐步降级
```

### 多层次限流架构

```
┌─────────────────────────────────────────────────────────┐
│                    多层限流防御体系                         │
│                                                         │
│  Layer 1: CDN / WAF                                     │
│    - IP 黑名单/白名单                                     │
│    - DDoS 防护                                           │
│    - 地域限流 (Geo-Rate Limiting)                        │
│                                                         │
│  Layer 2: API Gateway / 反向代理 (Nginx/Kong/Envoy)        │
│    - IP 级别限流 (每IP每秒N个连接)                         │
│    - 全局 QPS 限制                                       │
│    - 连接数限制                                          │
│                                                         │
│  Layer 3: 应用层限流器 (本文核心)                           │
│    - 用户级别限流                                         │
│    - API Key 级别限流                                    │
│    - 端点/资源级别限流                                     │
│    - 多维度组合限流 (用户 + API + 时间窗口)                  │
│                                                         │
│  Layer 4: 业务层限流                                      │
│    - 业务特定的限制 (例如: 每天最多发 100 封邮件)            │
│    - 用户等级差异化限流 (免费用户 vs 付费用户)               │
│    - 基于费用的限流                                       │
└─────────────────────────────────────────────────────────┘
```

### 限流键设计模式

```
模式1: 单维度限流
  - key: "rl:{user_id}:{api_endpoint}"
  - 示例: "rl:user123:/api/send_msg"
  - 限制: 每个用户对每个 API 的独立限流

模式2: 层级限流 (Hierarchical Rate Limiting)
  - key: "rl:{user_id}:{api_endpoint}"  → 用户级别，100/分钟
  - key: "rl:{user_id}:*"               → 用户全局，1000/分钟
  - key: "rl:*:{api_endpoint}"          → API全局，10000/分钟
  - 检查时按最细粒度 → 最粗粒度逐级检查

模式3: 时段限流
  - key: "rl:user123:peak"  → 高峰期限制 (8:00-22:00)
  - key: "rl:user123:offpeak" → 非高峰期限制 (22:00-8:00)
  - 根据当前时间选择不同的限流键

模式4: 滑动窗口 + 令牌桶混合
  - 先用滑动窗口计数器做粗粒度限流 (100/分钟)
  - 再用令牌桶做细粒度限流 (10/秒 burst + 2/秒 rate)
```

---

## 扩展性与高可用

### Redis 集群扩展

```
┌─────────────────────────────────────────────┐
│           Redis Cluster 架构                  │
│                                             │
│  Redis Cluster (3主3从 或 6主6从)             │
│  - 16384 个哈希槽分布在各节点                  │
│  - Key: {hashtag}:... 确保相关 Key 在同一分片  │
│  - 使用 CRC16 哈希路由                        │
│                                             │
│  水平扩展:                                    │
│    - 增加节点 → 重新分配哈希槽 → 数据迁移       │
│    - 在线迁移 (redis-cli --cluster reshard)  │
│                                             │
│  高可用:                                     │
│    - 每个主节点配一个从节点                     │
│    - Sentinel 自动故障转移                    │
│    - 故障转移时间 < 30s                       │
└─────────────────────────────────────────────┘
```

### 本地缓存优化

```
两阶段限流检查 (Two-Phase Rate Check):

Phase 1: 本地内存检查 (Caffeine/LRU Cache)
  - 缓存最近 N 秒的限流状态
  - 如果本地计数器 < 本地阈值 → 直接放行
  - 本地阈值 = 远程阈值 × 0.8 (保守策略)
  - 延迟: ~0.01ms

Phase 2: 远程 Redis 检查
  - 如果超过本地阈值 → 查询 Redis 精确限流
  - 异步同步 Redis 计数到本地
  - 延迟: ~1ms

效果: 80%+ 的请求在 Phase 1 处理, 大幅降低 Redis 调用

代码示意:
```python
class TwoPhaseRateLimiter:
    def __init__(self, local_threshold_ratio=0.8):
        self.local_cache = LocalCache()  # Caffeine/LRU
        self.redis = RedisClient()
        self.ratio = local_threshold_ratio

    def is_allowed(self, key, threshold, window_seconds):
        local_count = self.local_cache.get_count(key)
        if local_count < threshold * self.ratio:
            self.local_cache.incr(key)
            return True

        return self.redis_check_and_update(key, threshold, window_seconds)
```
```

### 监控与告警

```
核心监控指标:

性能指标:
  - 限流检查延迟 P50/P95/P99 (阈值: P99 > 5ms 告警)
  - Redis 调用延迟 P99
  - 本地缓存命中率 (阈值: < 70% 告警)

限流效果:
  - 限流触发率 (429 响应比例) (阈值: > 10% 告警，可能攻击)
  - 按用户/IP 的限流 Top-N (识别滥用来源)
  - 按 API 端点的限流分布

Redis 健康:
  - Redis 连接数、命令数
  - Redis 内存使用率 (阈值: > 80% 告警)
  - Redis 主从延迟 (阈值: > 1s 告警)
  - Key 淘汰数量 (Evictions)

业务指标:
  - 各 tier 用户的限流体验 (免费 vs 付费)
  - 误限率 (合法请求被拒绝的比例)
  - 漏限率 (应被限制但通过的请求比例)
```

---

## 总结

限流器是分布式系统中保护后端服务的核心组件，设计关键点包括：

1. **算法选择**：滑动窗口计数器 (Sliding Window Counter) 在精度和性能间达到最佳平衡，是生产环境的主流选择。令牌桶支持突发流量，适合大多数 API 场景
2. **原子性保证**：Redis Lua 脚本是分布式限流的利器，所有操作在服务端单线程原子执行
3. **多层次限流**：CDN → Gateway → 应用层 → 业务层 四层防御，层层递进
4. **本地缓存优化**：两阶段检查可将 Redis 调用减少 80%+，大幅降低延迟
5. **故障策略**：Fail-open vs Fail-close 取决于业务优先级，推荐混合策略
6. **限流键设计**：支持多维度（用户、API、IP、时段、等级）的组合限流
7. **监控驱动**：限流效果需要通过监控不断调优，避免误限和漏限

**面试核心权衡讨论：**
- 固定窗口 vs 滑动窗口：边界突发问题的深度理解
- Token Bucket vs Sliding Window Counter：突发支持 vs 平滑限流
- 分布式一致性：Redis 作为中心化计数器 vs 本地令牌同步方案
- 精度 vs 性能：近似算法（Sliding Window Counter）vs 精确算法（Sliding Window Log）
- 故障模式：fail-open vs fail-close 的业务影响分析
- 单机限流 vs 分布式限流：何时需要分布式，同步机制的代价
