# 45. 设计分片计数器 (Design Sharded Counter Service)

## 题目

设计高并发分布式计数器服务，用于统计社交媒体上的点赞数、播放量、分享数等。核心挑战：极高并发写入下保持计数的准确性与可扩展性。类似 Twitter Like Count、YouTube View Count、Reddit Upvote Count。

## 需求澄清

### 功能性需求

1. **递增/递减计数**: 对指定计数器 +1 或 -1
2. **查询计数**: 获取计数器的当前值
3. **批量查询**: 一次查询多个计数器（如帖子列表页）
4. **重置计数器**: 将计数器重置为 0 或指定值
5. **带 TTL 的计数器**: 过期自动清零（如 24 小时热度）
6. **Top-K 排行榜**: 查询计数最高的 Top-N

### 非功能性需求

1. **高并发写入**: 100K+ 写入/秒（单个计数器），整体支持百万级 QPS
2. **低延迟读取**: P99 < 5ms
3. **最终一致性**: 写入后可接受秒级延迟读到最新值
4. **水平扩展**: 支持亿级计数器
5. **高可用**: 99.99%，单节点故障不影响

### 容量估算

```
10 亿个活跃计数器，每计数器日均 100 次写入
日均写入: 10亿 × 100 = 1000亿次
平均写入 QPS: 1000亿 / 86400 ≈ 1.16M
峰值写入 QPS (10x): ≈ 11.6M
读取 QPS (写入的 3x): 约 3.5M 平均 / 35M 峰值

存储 (内存):
每个计数器元数据 ~100 bytes
10亿 × 100B = 100GB
如果每个计数器 10 个分片: 约 1TB Redis 内存

存储 (持久化):
最终计数: 8 bytes × 10亿 = 8GB
时间序列: 每天每计数器 1 点 × 365天 ≈ 额外 30GB
```

## API设计

```protobuf
service CounterService {
  rpc Increment(IncrementReq) returns (IncrementResp);
  rpc BatchIncrement(BatchIncrementReq) returns (BatchIncrementResp);
  rpc GetCount(GetCountReq) returns (GetCountResp);
  rpc BatchGetCount(BatchGetCountReq) returns (BatchGetCountResp);
  rpc Reset(ResetReq) returns (ResetResp);
  rpc GetTopK(GetTopKReq) returns (GetTopKResp);
}

message IncrementReq {
  string entity_type = 1;       // "post","video","comment"
  string entity_id = 2;
  int64 delta = 3;              // 默认1, 可为负
  string idempotency_key = 4;   // 幂等键
}

message BatchGetCountReq {
  message CounterKey {
    string entity_type = 1;
    string entity_id = 2;
  }
  repeated CounterKey keys = 1;
}

message GetTopKReq {
  string entity_type = 1;
  int32 k = 2;                  // Top K (默认100)
  string time_range = 3;        // "24h","7d","30d","all"
}
```

## 数据模型

### 分片计数器的核心思想

```
问题: 单 Redis Key counter:post:123 在高并发下成为瓶颈 (Redis 单线程 ~100K QPS)

分片方案:
  counter:post:123:shard:0  → 1000
  counter:post:123:shard:1  → 2000
  ...
  counter:post:123:shard:N-1 → 1500

  写: 随机选分片 INCR
  读: 所有分片求和
  写入吞吐 ↑ N 倍 (N = 分片数)
```

### MySQL 持久化模型

```sql
CREATE TABLE counters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    count BIGINT NOT NULL DEFAULT 0,
    version INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_entity (entity_type, entity_id),
    INDEX idx_count (entity_type, count)
) ENGINE=InnoDB;

CREATE TABLE counter_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    delta INT NOT NULL,
    idempotency_key VARCHAR(128),
    shard_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_idempotency (idempotency_key)
) ENGINE=InnoDB
PARTITION BY RANGE (TO_DAYS(created_at)) (...) ;

CREATE TABLE leaderboard_snapshot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    rank INT NOT NULL,
    count BIGINT NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    INDEX idx_type_rank (entity_type, rank)
) ENGINE=InnoDB;
```

### Redis 数据结构

```
# 分片计数器
cnt:{type}:{id}:shard:{N}  →  value (int)
# 随机分片写, 全分片求和读

# 排行榜 Sorted Set
ZADD leaderboard:{type}:all {id} {count}
ZREVRANGE leaderboard:{type}:all 0 99 WITHSCORES

# 按时间窗口的排行榜
ZADD leaderboard:{type}:24h {id} 1500
ZADD leaderboard:{type}:7d  {id} 8500

# 幂等去重
SET idempotency:counter:{key} "1" NX EX 3600
```

## 高层次架构

```
                        ┌──────────────────┐
                        │   Client / API    │
                        └────────┬─────────┘
                        ┌────────▼─────────┐
                        │  Counter Service  │
                        │ ┌───────────────┐ │
                        │ │ Write Router  │ │ ← 随机选择分片
                        │ │ Shard Manager │ │ ← 自适应分片数
                        │ └───────┬───────┘ │
                        └─────────┼─────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
   ┌────▼───┐ ┌────▼───┐ ┌────▼───┐                   ┌────▼───┐
   │Redis   │ │Redis   │ │Redis   │     ...           │Redis   │
   │Shard 0 │ │Shard 1 │ │Shard 2 │                   │Shard M │
   └────┬───┘ └────┬───┘ └────┬───┘                   └────┬───┘
        └──────────┼──────────┼───────────────────────────┘
                   │ 定期刷盘 (10s 或 N 次写入)
              ┌────▼──────────────────────┐
              │     Async Flush Service    │
              │  聚合分片求和 → MySQL 持久化│
              └────────────┬──────────────┘
                   ┌───────▼───────┐
                   │  MySQL Cluster│
                   │ (持久化+排行榜)│
                   └───────────────┘
```

### 写入流程

```
1. Client → Counter Service
2. 幂等检查 (idempotency_key)
3. 确定分片数 (自适应: 热门 vs 冷门)
4. 随机选分片: cnt:{type}:{id}:shard:{random(N)}
5. INCRBY 写入 Redis → 立即返回
6. 异步: Kafka counter_log (对账用)
7. 异步刷盘: 聚合分片 → MySQL
```

## 核心深入

### 方案对比：分片策略

#### 方案A: 固定分片数

```python
SHARD_COUNT = 10

def increment(entity_type, entity_id, delta=1):
    shard = random.randint(0, SHARD_COUNT - 1)
    key = f"cnt:{entity_type}:{entity_id}:shard:{shard}"
    redis.incrby(key, delta)

def get_count(entity_type, entity_id):
    keys = [f"cnt:{entity_type}:{entity_id}:shard:{i}"
            for i in range(SHARD_COUNT)]
    return sum(int(v or 0) for v in redis.mget(keys))
```

**优点**: 简单，写入吞吐提升 N 倍
**缺点**: 所有计数器都占 N 倍内存，冷门浪费

#### 方案B: 自适应分片 (推荐)

```python
class AdaptiveShardCounter:
    MIN_SHARDS = 1
    MAX_SHARDS = 1024

    def get_shard_count(self, entity_type, entity_id):
        rate_key = f"cnt:rate:{entity_type}:{entity_id}"
        write_rate = int(redis.get(rate_key) or 0)

        if write_rate < 100:       return 1
        elif write_rate < 1000:    return 4
        elif write_rate < 10000:   return 16
        elif write_rate < 100000:  return 64
        else:                      return min(256, self.MAX_SHARDS)

    def increment(self, entity_type, entity_id, delta=1):
        shard_count = self.get_shard_count(entity_type, entity_id)
        shard = random.randint(0, shard_count - 1)
        key = f"cnt:{entity_type}:{entity_id}:shard:{shard}"
        redis.incrby(key, delta)
        # 更新写入速率 (10s滑动窗口)
        rate_key = f"cnt:rate:{entity_type}:{entity_id}"
        redis.incr(rate_key)
        redis.expire(rate_key, 10)

    def get_count(self, entity_type, entity_id):
        shard_count = self.get_shard_count(entity_type, entity_id)
        keys = [f"cnt:{entity_type}:{entity_id}:shard:{i}"
                for i in range(shard_count)]
        return sum(int(v or 0) for v in redis.mget(keys))
```

#### 三种方案对比

| 方案 | 写入吞吐 | 内存效率 | 读延迟 | 复杂度 |
|------|---------|---------|--------|--------|
| 单Key | 100K QPS | 最佳 | 1次GET | 极低 |
| 固定分片 | N×100K QPS | 差 | N次GET | 低 |
| 自适应分片 | 动态调整 | 好 | 动态 | 中 |

### Redis Lua 原子操作

```lua
-- 自适应分片递增 (服务端原子操作)
local rate_key = KEYS[1]
local count_prefix = KEYS[2]
local delta = tonumber(ARGV[1])
local max_shards = tonumber(ARGV[2])

-- 确定分片数
local write_rate = redis.call('INCR', rate_key)
redis.call('EXPIRE', rate_key, 10)

local shard_count = 1
if write_rate > 100000 then shard_count = 256
elseif write_rate > 10000 then shard_count = 64
elseif write_rate > 1000 then shard_count = 16
elseif write_rate > 100 then shard_count = 4
end
if shard_count > max_shards then shard_count = max_shards end

-- 随机分片递增
local shard_id = math.random(0, shard_count - 1)
local new_val = redis.call('INCRBY', count_prefix .. ':shard:' .. shard_id, delta)

return {write_rate, shard_count, shard_id, new_val}
```

### Top-K 排行榜设计

| 方案 | 实时性 | 精确度 | 内存 | 适用场景 |
|------|--------|--------|------|---------|
| Redis Sorted Set | 实时 | 精确 | 大 | < 百万级 |
| 分桶近似 Top-K | 实时 | 近似 | 中 | 亿级 |
| 异步批处理 + DB | 分钟级 | 精确 | 小 | 任意规模 |

**推荐**: 异步批处理 + DB 查询方案 (大部分排行榜场景接受分钟级延迟)

```
-- 每 5 分钟执行
SELECT entity_id, count FROM counters
WHERE entity_type = 'post'
ORDER BY count DESC LIMIT 500;

-- 写入 leaderboard_snapshot 和 Redis 缓存
```

### 幂等性与去重

```python
def increment_with_idempotency(entity_type, entity_id, delta, idempotency_key):
    # Layer 1: Redis SETNX 快速去重
    dedup_key = f"idem:{entity_type}:{entity_id}:{idempotency_key}"
    if not redis.set(dedup_key, "1", nx=True, ex=300):
        return "DUPLICATE"

    # Layer 2: DB unique约束防Redis宕机丢失
    try:
        db.insert_counter_log(entity_type, entity_id, delta, idempotency_key)
    except DuplicateKeyError:
        return "DUPLICATE"

    return increment(entity_type, entity_id, delta)
```

### 视频播放计数特殊处理

```python
def count_video_view(video_id, user_id, watch_duration):
    if watch_duration < 3:        # 观看不足3秒不计数
        return "TOO_SHORT"
    # 同一用户同一视频30分钟内只计1次
    dedup_key = f"view:dedup:{video_id}:{user_id}"
    if not redis.set(dedup_key, "1", nx=True, ex=1800):
        return "ALREADY_COUNTED"
    return increment("video", video_id, 1)
```

## 扩展性与高可用

### 对账系统 (Reconciliation)

```
目标: 确保 Redis 分片聚合值 == MySQL 值

流程:
  1. 每小时从 MySQL 读所有计数器值
  2. 从 Redis 聚合所有分片求和
  3. 对比差异:
     - 差异小: 自动修复 (MySQL值覆盖Redis)
     - 差异大: 告警人工介入
  4. 采样对账: 每次写入1%对比，差异率>阈值触发全量对账
```

### 降级策略

| Level | 措施 | 影响 |
|-------|------|------|
| 0 (正常) | 自适应分片 + 实时聚合 + 排行榜 | 无 |
| 1 | 固定分片数 | 热点计数器可能降级 |
| 2 | 关闭实时排行榜, 切T+5min离线 | 排行榜延迟5分钟 |
| 3 | 写入异步化: Client→Kafka→异步消费, 读MySQL | 数据延迟10s+ |
| 4 | 只读不写, 返回缓存值 | 数据不再更新 |

### CAP分析

计数器系统可选择 **AP**:
- 不要求强一致性（秒级最终一致即可）
- 写入 Redis 分片立即返回，异步刷盘 MySQL
- 网络分区时继续服务（AP），分区恢复后对账修复

## 总结

1. **分片是核心**: 单 Redis Key 瓶颈 → 分片计数器 → 写入吞吐提升 N 倍
2. **自适应分片**: 冷门计数器 1 分片（省内存），热门动态扩展到 256 分片
3. **Lua 原子操作**: 分片选择 + 递增在 Redis 服务端原子完成
4. **Write-Behind**: Redis 同步写 → 异步批量刷 MySQL，低延迟 + 可靠持久化
5. **幂等双保险**: Redis SETNX + DB unique constraint
6. **排行榜异步化**: 5 分钟批处理，精确且内存友好
7. **对账修复**: 定时对比 Redis vs MySQL，自动修复差异
8. **特殊场景**: 视频播放需观看时长 + 用户去重窗口

面试中可能追问: 分片调整时如何保证计数不丢失? 分片数从10调整到20的迁移方案?
