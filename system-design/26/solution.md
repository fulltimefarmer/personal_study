# 设计排行榜系统 (Design Leaderboard System)

## 题目

设计一个游戏排行榜系统，支持实时更新玩家分数、查询排名、Top K玩家、附近排名等功能。

## 需求澄清

### 功能性需求

1. **分数更新**: 玩家完成游戏后更新分数(支持覆盖和增量两种模式)
2. **排名查询**: 查询某玩家的排名和分数
3. **Top K查询**: 查询排行榜前N名玩家
4. **区间排名**: 查询某玩家"周围"的排名(上下各N名)
5. **多排行榜**: 支持按不同维度(全服、好友、地区、月榜、周榜)
6. **历史榜单**: 查看历史排行榜(昨天的榜单、上周的榜单)
7. **时间窗口**: 支持周榜、月榜自动重置

### 非功能性需求

- **实时性**: 分数更新后 < 1秒反映到排行榜
- **高并发**: 支持 100K+ QPS 分数更新操作
- **低延迟**: 排名查询 < 5ms
- **准确性**: 分数和排名必须精确(不能用近似算法算排名)
- **扩展性**: 支持亿级玩家
- **高可用**: 99.99%

### 容量估算

```
假设:
- 游戏DAU: 5000万
- 平均每人每天玩5局 → 2.5亿次分数更新
- 峰值QPS: 2.5亿 / 86400 × 5(高峰系数) ≈ 14,500 QPS
- 排行榜查询QPS: 约是更新的3倍 → ~43,500 QPS

存储估算:
- 全服排行榜: 5000万玩家
- 每个排行榜条目: player_id(8B) + score(8B) + nickname(32B) ≈ 48B
- 单个排行榜: 5000万 × 48B ≈ 2.4 GB
- 带历史榜单(30天) + 地区榜(10个) + 好友榜(活跃玩家) → ~100 GB
- 加上sorted set元数据开销 → ~250 GB
```

## API设计

```protobuf
// 更新分数
// POST /api/v1/leaderboard/score
message UpdateScoreRequest {
  string leaderboard_id = 1;           // "global", "weekly_2024W30", "region_US"
  string user_id = 2;
  int64 score = 3;                     // 新分数
  UpdateMode mode = 4;                 // 更新模式
  map<string, string> metadata = 5;    // 额外信息(昵称、头像等)
}

enum UpdateMode {
  OVERWRITE = 0;                       // 覆盖：score = new_score
  INCREMENT = 1;                       // 增量：score += delta
  MAX = 2;                             // 取最大值：score = max(score, new_score)
}

message UpdateScoreResponse {
  string user_id = 1;
  int64 new_score = 2;
  int64 rank = 3;                      // 新排名
  int64 percentile = 4;                // 百分位(前X%)
}

// 查询排行榜 Top-K
// GET /api/v1/leaderboard/{leaderboard_id}/top?start=0&end=100
message TopKResponse {
  string leaderboard_id = 1;
  int64 total_players = 2;
  repeated LeaderboardEntry entries = 3;
}

message LeaderboardEntry {
  int64 rank = 1;
  string user_id = 2;
  int64 score = 3;
  map<string, string> metadata = 4;
  int64 updated_at_ms = 5;
}

// 查询玩家排名
// GET /api/v1/leaderboard/{leaderboard_id}/rank/{user_id}
message RankResponse {
  string user_id = 1;
  int64 score = 2;
  int64 rank = 3;                      // 1-based排名
  int64 total_players = 4;
  double percentile = 5;
}

// 查询附近排名
// GET /api/v1/leaderboard/{leaderboard_id}/nearby/{user_id}?count=10
message NearbyResponse {
  repeated LeaderboardEntry above = 1; // 排名比用户高的玩家
  LeaderboardEntry current = 2;
  repeated LeaderboardEntry below = 3; // 排名比用户低的玩家
}

// 获取历史榜单
// GET /api/v1/leaderboard/history?leaderboard_id=weekly_2024W29
```

## 数据模型

### Redis Sorted Set 方案 (核心)

```redis
# Redis Sorted Set 完美匹配排行榜需求
# 
# 数据结构:
#   Key: leaderboard:{leaderboard_id}
#   Member: user_id (或 user_id:metadata 的组合)
#   Score: 玩家分数 (float64)

# 分数更新
ZADD leaderboard:global 9500 player_1001
# 返回: 被更新的元素数量

# 查询排名 (0-based, 从高到低 = rev)
ZREVRANK leaderboard:global player_1001
# 返回: 0 (第1名) 或 nil (不存在)

# 查询分数
ZSCORE leaderboard:global player_1001
# 返回: "9500"

# 查询Top 100
ZREVRANGE leaderboard:global 0 99 WITHSCORES
# 返回: ["player_1001","9500","player_2002","9400",...]

# 查询附近排名 (当前排名附近10名)
ZREVRANGE leaderboard:global <rank-5> <rank+5> WITHSCORES

# 查询指定分数范围的排名
ZREVRANGEBYSCORE leaderboard:global 10000 5000 WITHSCORES LIMIT 0 20

# 排行榜总人数
ZCARD leaderboard:global
# 返回: 50000000

# 获取百分位
# rank / card * 100
```

### 排行榜元数据存储 (MySQL)

```sql
CREATE TABLE leaderboards (
    leaderboard_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type ENUM('global', 'regional', 'weekly', 'monthly', 'friends', 'guild') NOT NULL,
    region VARCHAR(50),                    -- NULL for global
    season_id VARCHAR(50),                 -- "2024W30", "2024M07"
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,                    -- NULL for permanent
    status ENUM('active', 'archived', 'expired') DEFAULT 'active',
    sort_order ENUM('desc', 'asc') DEFAULT 'desc',  -- 降序(分数高排前) / 升序(时间少排前)
    total_players BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type_status (type, status)
);

CREATE TABLE leaderboard_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    leaderboard_id VARCHAR(64) NOT NULL,
    snapshot_date DATE NOT NULL,
    total_players BIGINT NOT NULL,
    top_players JSON,                      -- [{rank:1, user_id:"", score:0}, ...]
    snapshot_size BIGINT NOT NULL,         -- 备份了多少条
    storage_path VARCHAR(500),             -- 完整快照的S3路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_leaderboard_date (leaderboard_id, snapshot_date)
);

CREATE TABLE user_profile_cache (
    user_id VARCHAR(64) PRIMARY KEY,
    nickname VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    country VARCHAR(50),
    level INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       排行榜系统架构                                      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         游戏服务器                                 │  │
│  │  游戏结束 → 计算分数 → 调用排行榜API                                │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                       │
│                                ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        API Gateway                                 │  │
│  │  (认证/限流/路由)                                                   │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                       │
│                    ┌───────────┼───────────┐                           │
│                    ▼           ▼           ▼                           │
│  ┌──────────────────────┐ ┌─────────┐ ┌──────────────┐               │
│  │ 分数写入服务           │ │排名查询 │ │榜单管理服务   │               │
│  │ (Score Writer)       │ │服务     │ │(Leaderboard  │               │
│  │                      │ │         │ │ Manager)     │               │
│  └──────────┬───────────┘ └────┬────┘ └──────┬───────┘               │
│             │                  │              │                        │
│             └──────────────────┼──────────────┘                       │
│                                │                                       │
│                    ┌───────────┼───────────┐                           │
│                    ▼           ▼           ▼                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        存储层                                      │  │
│  │                                                                   │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │  │
│  │  │ Redis Cluster    │  │ Redis Stream +   │  │ MySQL / S3     │  │  │
│  │  │ (主排行榜存储)    │  │  Kafka           │  │ (历史榜单/     │  │  │
│  │  │                  │  │ (异步榜单同步)    │  │  玩家元数据)   │  │  │
│  │  │ Sorted Set 存储  │  │                  │  │                │  │  │
│  │  │ 全服/周榜/地区榜  │  │ 订阅更新事件     │  │ 每日快照       │  │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      定时任务 (Cron Jobs)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │  │
│  │  │ 周榜/月榜重置  │  │ 每日快照导出  │  │ 历史榜单归档到S3     │    │  │
│  │  │ (周一0点)     │  │ (凌晨3点)     │  │ (压缩后长期保留)     │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. Redis Sorted Set 底层原理

```
┌────────────────────────────────────────────────────────────────┐
│              Redis Sorted Set 内部实现                          │
│                                                                │
│  Redis Sorted Set 使用两种数据结构:                             │
│                                                                │
│  1. Skip List (跳表) - 用于按score排序                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Skip List 时间复杂度:                                    │  │
│  │  - 插入/删除/更新: O(log N)                               │  │
│  │  - 按排名查询: O(log N)                                   │  │
│  │  - 按分数范围查询: O(log N + M) (M=返回数量)              │  │
│  │                                                          │  │
│  │  结构示意:                                                │  │
│  │  Level 3:  HEAD ────────────────────► NODE_A ──► NULL   │  │
│  │  Level 2:  HEAD ───────► NODE_B ────► NODE_A ──► NULL   │  │
│  │  Level 1:  HEAD ─► NODE_C ─► NODE_B ─► NODE_A ─► NULL  │  │
│  │  Level 0:  HEAD ─► NODE_C ─► NODE_B ─► NODE_D ─► NODE_A │  │
│  │                          │                     │          │  │
│  │                     (score=100)          (score=9500)     │  │
│  │                                                          │  │
│  │  层级随机生成 (概率50%升级), 平均探索路径 O(log N)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  2. Hash Table - 用于按member快速定位                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  member → (score, skip_list_node)                         │  │
│  │  支持 O(1) 查找特定member的score和排名节点                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  内存占用估算:                                                  │
│  - 每个 member ≈ 80 bytes (overhead + member指针 + score)     │
│  - 5000万玩家 × 80B ≈ 4 GB (仅索引)                           │
│  - 加上 member字符串(假设平均16B) × 5000万 ≈ 800 MB           │
│  - 总计约 5 GB (单个排行榜)                                   │
│  - Redis Cluster 内存: 5 GB × 副本3 × 排行榜数 × 1.5开销      │
└────────────────────────────────────────────────────────────────┘
```

### 2. 大规模排行榜的分片策略

```
┌────────────────────────────────────────────────────────────────┐
│              超大排行榜的分片方案                                │
│                                                                │
│  问题: 单个 Redis Sorted Set 存储 5亿玩家?                      │
│  - 内存: ~50 GB, 单实例内存不足                                 │
│  - CPU: 单线程处理所有操作成为瓶颈                               │
│                                                                │
│  方案一: Redis Cluster 自动分片 (槽位分配)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  Key: leaderboard:global:{hash_slot}                      │  │
│  │  Redis Cluster 按 key hash → 16384 个slot自动分布          │  │
│  │                                                          │  │
│  │  问题: Sorted Set 的跨slot操作不支持!                      │  │
│  │  ZUNIONSTORE 不能跨slot, ZRANGE 只能在单个slot内           │  │
│  │                                                          │  │
│  │  解决: Hash Tag - 使用 {} 强制同一个slot:                 │  │
│  │  Key: leaderboard:global:{shard_id}                       │  │
│  │  将排行榜人工分成N个分片，每个分片一个Sorted Set           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  方案二: 分桶 (Sharding Buckets) - 推荐                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  将玩家按 hash(user_id) % N 分到N个bucket                 │  │
│  │                                                          │  │
│  │  Bucket 0: leaderboard:global:bucket0 (约 5000万/N 玩家) │  │
│  │  Bucket 1: leaderboard:global:bucket1                     │  │
│  │  ...                                                      │  │
│  │  Bucket N-1: leaderboard:global:bucketN-1                 │  │
│  │                                                          │  │
│  │  写入:                                                    │  │
│  │    bucket = hash(user_id) % N                             │  │
│  │    ZADD leaderboard:global:bucket{bucket} user_id score   │  │
│  │                                                          │  │
│  │  查询玩家排名:                                            │  │
│  │    1. 本地排名:                                          │  │
│  │       local_rank = ZREVRANK lb:bucket user_id            │  │
│  │    2. 统计其他bucket中比该玩家分数高的人数:                │  │
│  │       higher_count = Σ ZCOUNT lb:bucket{i} (score+1, +inf)│
│  │    3. 全局排名 = local_rank + higher_count + 1           │  │
│  │                                                          │  │
│  │  优化: 每个bucket维护一个 sorted high_score 列表          │  │
│  │  定期(每分钟)更新每个bucket的分数分布摘要                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  方案三: 两阶段查询 (适合读多写少)                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Phase 1: 热榜 (Top 1000) → 单独存储, 完全精确            │  │
│  │  Phase 2: 全榜 → 分片存储, 允许秒级延迟                   │  │
│  │                                                          │  │
│  │  接入策略:                                                │  │
│  │  - Top K 查询 → 只查热榜                                  │  │
│  │  - 个人排名 → 查分片 + 汇总                                │  │
│  │  - 百分位 → 使用 HyperLogLog 或分片统计                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 3. 时间窗口排行榜 (周榜/月榜)

```
┌────────────────────────────────────────────────────────────────┐
│              时间窗口排行榜实现                                  │
│                                                                │
│  挑战: 如何在0点瞬间切换周榜?                                    │
│                                                                │
│  方案: 滚动窗口 + 双Buffer                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  周榜 Key 命名:                                           │  │
│  │  leaderboard:weekly:2024W30                              │  │
│  │  leaderboard:weekly:2024W31                              │  │
│  │                                                          │  │
│  │  时间线:                                                  │  │
│  │  ─────────────────────────────────────────►              │  │
│  │  Mon 0:00       Mon 0:00 (下周)                           │  │
│  │    │              │                                       │  │
│  │    │ Week 30      │ Week 31                              │  │
│  │    │              │                                       │  │
│  │  写入: 总是写到当前周对应的key                              │  │
│  │  查询: 默认查当前周, 支持查历史周                            │  │
│  │                                                          │  │
│  │  周一0点切换逻辑:                                          │  │
│  │  1. Cron job 触发                                         │  │
│  │  2. RENAME leaderboard:weekly:current →                   │  │
│  │          leaderboard:weekly:2024W30                       │  │
│  │  3. 导出 leaderboard:weekly:2024W30 快照到S3              │  │
│  │  4. 删除 leaderboard:weekly:2024W30 (延迟7天)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  双Buffer方案 (零停机时间):                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  当前周期内始终维持两个Sorted Set:                         │  │
│  │  - leaderboard:weekly:active:0 (主)                      │  │
│  │  - leaderboard:weekly:active:1 (备)                      │  │
│  │                                                          │  │
│  │  切换逻辑:                                                │  │
│  │  1. 写操作同时写 active:0 和 active:1                     │  │
│  │  2. 读操作指向 active:0                                   │  │
│  │  3. 00:00 → 原子切换读指针到 active:1                     │  │
│  │  4. 将 active:0 归档 → 清空 → 下一周期作为备              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4. 历史榜单存储

```
┌────────────────────────────────────────────────────────────────┐
│              历史榜单快照与导出                                  │
│                                                                │
│  每日快照导出流程:                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  1. 每日凌晨3点 (低峰)                                    │  │
│  │  2. 扫描 Redis Sorted Set, 分批导出 (SCAN/Cursor)        │  │
│  │  3. 转为 Parquet 格式压缩后上传 S3                        │  │
│  │     - 按排名分区: rank_range=1_10000, 10001_20000, ...   │  │
│  │  4. 更新 leaderboard_history 表记录快照元数据             │  │
│  │                                                          │  │
│  │  导出代码 (批量读取, 避免阻塞):                            │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ cursor = 0                                          │  │
│  │  │ batch_size = 10000                                  │  │
│  │  │ while cursor != 0 or start:                         │  │
│  │  │     cursor, items = ZSCAN(key, cursor,              │  │
│  │  │                          COUNT=batch_size)          │  │
│  │  │     # items: [member1, score1, member2, score2,...]│  │
│  │  │     write_to_parquet(items, batch_index)            │  │
│  │  │     batch_index++                                    │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  查询历史榜单:                                            │  │
│  │  - 如果查询最近7天 → 从 Redis 热数据查                    │  │
│  │  - 如果查询7天以上 → 从 S3 (Parquet) 查                   │  │
│  │    → Athena/Presto 做 SQL 查询                          │  │
│  │    → 延迟可能100ms-1s                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. 好友排行榜 / 公会排行榜

```
┌────────────────────────────────────────────────────────────────┐
│              好友/公会排行榜实现                                  │
│                                                                │
│  挑战: 好友榜不是固定集合，好友关系动态变化                       │
│                                                                │
│  方案一: 在Redis中临时聚合                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────┐          │
│  │  1. 获取用户的好友列表 (MySQL/Redis Set)          │          │
│  │  2. 每个好友在 Sorted Set 中查分数                │          │
│  │  3. 客户端排序展示                                │          │
│  │                                                  │          │
│  │  问题: 好友1000人 → 1000次 ZSCORE → 延迟高     │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                │
│  方案二: 为每个玩家维护独立的Sorted Set                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Key: friends_leaderboard:{user_id}               │          │
│  │  好友增删时, 更新该key对应的成员                    │          │
│  │                                                  │          │
│  │  问题: 好友有1000人, 每个人平均100好友              │          │
│  │  → 好友变更需要更新100个Sorted Set                │          │
│  │  → 好友变更和分数更新耦合                         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                │
│  方案三: 单写多读 + Pipeline优化 (推荐)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  ┌──────────────────────────────────────────────────┐          │
│  │  1. Redis Pipeline 批量查询好友分数:               │          │
│  │     pipeline = redis.pipeline()                   │          │
│  │     for friend_id in friends:                     │          │
│  │         pipeline.zrevrank(f"lb:global", friend_id)│          │
│  │         pipeline.zscore(f"lb:global", friend_id)  │          │
│  │     results = pipeline.execute()                  │          │
│  │                                                  │          │
│  │  2. 服务器端排序后返回 (避免客户端排序)             │          │
│  │  3. 缓存结果: cache:friends_rank:{user_id}        │          │
│  │     TTL: 30秒 (允许排行榜稍延迟)                  │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                │
│  公会排行榜:                                                    │
│  - 每个公会维护一个 Sorted Set: guild_leaderboard:{guild_id}    │
│  - 公会分数 = SUM(公会成员分数) 或 TOP N 成员分数和              │
│  - 公会在全局公会榜的排名另维护一个 Sorted Set                    │
└────────────────────────────────────────────────────────────────┘
```

### 6. 防作弊与公平性

```
┌────────────────────────────────────────────────────────────────┐
│                    防作弊措施                                    │
│                                                                │
│  1. 分数校验:                                                   │
│     - 服务端计算分数 (不信任客户端上报)                          │
│     - 分数必须在合理范围内 (单局最高分上限)                      │
│     - 时间验证: 游戏时长与分数匹配                              │
│                                                                │
│  2. 更新频率限制:                                               │
│     - 同一用户每秒最多更新1次                                    │
│     - Redis: rate_limit:score_update:{user_id}                │
│       INCR → 超过限制则拒绝                                     │
│                                                                │
│  3. 异常检测:                                                   │
│     - 分数突变检测 (历史分数pattern)                             │
│     - 设备/IP关联检测 (多账号刷分)                               │
│                                                                │
│  4. 审计日志:                                                   │
│     - 所有分数变更记录到 MySQL 审计表                            │
│     - 支持回溯查证                                               │
└────────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### Redis 高可用方案

```
┌──────────────────────────────────────────────────────────────┐
│                 Redis 排行榜高可用                             │
│                                                              │
│  方案一: Redis Sentinel (哨兵)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐                  │   │
│  │  │Master  │  │Slave 1 │  │Slave 2 │                  │   │
│  │  │(写)   │──►(读)    │──►(读)    │                  │   │
│  │  └────────┘  └────────┘  └────────┘                  │   │
│  │       ▲                                               │   │
│  │       │ 监控 + 自动故障转移                            │   │
│  │  ┌────────────────────────┐                          │   │
│  │  │ Sentinel Node × 3      │                          │   │
│  │  │ (Quorum=2 决策切主)    │                          │   │
│  │  └────────────────────────┘                          │   │
│  │                                                      │   │
│  │  缺点: 切换期间短暂不可写(秒级)                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  方案二: Redis Cluster (推荐)                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│  │  │Shard 0  │  │Shard 1  │  │Shard 2  │               │   │
│  │  │Master   │  │Master   │  │Master   │               │   │
│  │  │Slave    │  │Slave    │  │Slave    │               │   │
│  │  └─────────┘  └─────────┘  └─────────┘               │   │
│  │                                                      │   │
│  │  自动分片 + 自动故障转移                               │   │
│  │  每个分片独立, 故障影响面小                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  读写分离:                                                    │
│  - 写操作 → Master                                           │
│  - Top K 查询 → Slave (允许轻微延迟)                         │
│  - 个人排名查询 → Master (需要强一致)                        │
│  - 利用 READONLY 命令从 Slave 读取                           │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 核心存储 | Redis Sorted Set | O(log N) 操作, SkipList 完美契合 |
| 分片策略 | 按 user_id hash 分桶 | 平滑扩展, 排名计算可并行汇总 |
| 高可用 | Redis Cluster + 主从复制 | 自动故障转移, 无单点 |
| 时间窗口 | 周/月维度命名 + 双Buffer | 零停机时间切换 |
| 历史榜单 | 每日快照 → S3 (Parquet) | 低成本长期存储 |
| 好友榜 | Pipeline批量查询 + 结果缓存 | 兼顾性能和实时性 |
| 防作弊 | 服务端校验 + 频率限制 + 异常检测 | 多维度防刷 |

核心设计要点:
1. **Redis Sorted Set 是天选数据结构**: O(log N) 的排名操作, 不需要自己实现
2. **超大规模需要分桶**: 单 Sorted Set 有内存和性能上限, hash分桶是标准做法
3. **全局排名的计算**: = 桶内排名 + 其他高分段桶统计, 可并行
4. **热榜分离**: Top 1000 单独存储保证热门查询精确低延迟
5. **时间窗口天然隔离**: 周榜/月榜用不同key, 切换只改路由不迁移数据
6. **历史数据降冷**: 热数据在Redis, 冷数据在S3, 按热度分层
