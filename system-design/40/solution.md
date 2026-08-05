# 40. 设计实时分析平台 (Real-time Analytics like ClickHouse/Druid)

## 题目
设计一个实时分析平台，支持大规模数据摄入、实时 OLAP 查询、多维聚合分析。类似 ClickHouse、Apache Druid、Apache Pinot、Google BigQuery。

---

## 需求澄清

### 功能性需求
- 支持实时数据摄入（Kafka/Stream 数据源），秒级延迟
- 支持批量数据导入（HDFS/S3），小时/天级别
- 多维聚合查询（GROUP BY, COUNT, SUM, AVG, MIN, MAX）
- 支持 TopN、漏斗分析、留存分析
- 支持预聚合（预计算 Cube/Rollup）
- 支持近似计算（HyperLogLog, DataSketches）
- SQL 查询接口
- 数据可视化对接（Grafana/Superset）
- 数据保留策略（TTL 自动删除过期数据）

### 非功能性需求

| 指标 | 要求 |
|------|------|
| 写入吞吐 | 百万 events/s |
| 查询延迟 | 简单查询 <100ms，复杂聚合 <1s |
| 数据新鲜度 | 实时模式延迟 <5s |
| 数据量 | PB级，日增 TB级 |
| 可用性 | 99.9% |
| 压缩比 | 10:1 以上 |

### 容量估算

假设：
- 每日事件数：100亿
- 每事件大小：压缩后 ~100B（列式 + 高压缩比）
- 每日存储：100亿 × 100B = 1TB（压缩后）
- 原始数据：100亿 × 1KB = 10TB（压缩前）
- 压缩比：~10:1（列式存储 + 字典编码 + 通用压缩）
- 30天保留：30TB
- 查询 QPS：1000（仪表板 + 手动查询）
- 写入 QPS：100亿 / 86400 ≈ 115,740 events/s

---

## 核心概念

### OLAP vs OLTP

```
┌─────────────────────────────────────────────────────────────────┐
│ OLTP (Online Transaction Processing) vs OLAP                     │
├────────────────┬────────────────────────────────────────────────┤
│ OLTP           │ 行存, 少量行读写, 事务, B+Tree, MySQL/PG       │
│ OLAP           │ 列存, 海量行扫描+聚合, 无事务, ClickHouse/Druid│
├────────────────┼────────────────────────────────────────────────┤
│ 行存 (Row):   │ ┌──┬──┬──┬──┐                                   │
│              │ │id│name│age│city│ → 适合查询全部列               │
│              │ └──┴──┴──┴──┘                                     │
│              │                                                    │
│ 列存 (Column):│ ┌────┬─────┐                                     │
│              │ │column_name│ → 只读需要的列，减少IO               │
│              │ ├────┼─────┤→ 同类型数据压缩率高(字典/Delta/RLE) │
│              │ │values...  │→ 向量化执行(SIMD)                   │
│              │ └────┴─────┘                                     │
└────────────────┴────────────────────────────────────────────────┘
```

### 数据模型

```sql
-- ClickHouse 建表示例
CREATE TABLE events (
    event_time      DateTime,
    event_type      LowCardinality(String),  -- page_view, click, purchase
    user_id         UInt64,
    session_id      String,
    page_url        String,
    referrer        String,
    device_type     LowCardinality(String),  -- mobile, desktop, tablet
    country         LowCardinality(String),
    duration_ms     UInt32,
    price           Decimal(10, 2),
    properties      String  -- JSON 扩展属性
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_type, event_time, user_id)
TTL event_time + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;
```

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Data Sources (数据源)                             │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ Kafka    │  │ App SDK  │  │ HDFS/S3  │  │ Database │                │
│  │ Stream   │  │ (埋点)    │  │ Batch    │  │ CDC      │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │              │             │              │                       │
└───────┼──────────────┼─────────────┼──────────────┼───────────────────────┘
        │              │             │              │
        ▼              ▼             ▼              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Ingestion Layer (摄入层)                            │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │ Real-time    │  │ Batch        │  │ Data         │                   │
│  │ Ingestion    │  │ Ingestion    │  │ Validator    │                   │
│  │ (Flink/Kafka Connect)│(Spark)  │  │ (Schema校验) │                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
│         │                 │                  │                            │
│         └─────────────────┼──────────────────┘                            │
│                           │                                              │
│                   Row → Columnar Format                                   │
│                   (行转列 → Parquet/ORC/Custom)                           │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      Storage & Query Engine                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Coordinator / Broker                            │   │
│  │                                                                  │   │
│  │  - 接收SQL查询 → 解析 → 优化 → 分发到 Data Nodes                    │   │
│  │  - 合并各节点结果 → 返回客户端                                      │   │
│  │  - 管理 Segment 分配和路由表(Segment → Node mapping)               │   │
│  └────────────────────────────┬─────────────────────────────────────┘   │
│                               │                                          │
│          ┌────────────────────┼────────────────────┐                     │
│          ▼                    ▼                    ▼                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                 │
│  │ Data Node 1  │   │ Data Node 2  │   │ Data Node N  │                 │
│  │              │   │              │   │              │                 │
│  │ Segment:     │   │ Segment:     │   │ Segment:     │                 │
│  │ [2024-01-01  │   │ [2024-01-02  │   │ [2024-01-03  │                 │
│  │  ~ 2024-01-03│   │  ~ 2024-01-04│   │  ~ 2024-01-05│                 │
│  │  Part0]      │   │  Part1]      │   │  Part2]      │                 │
│  │              │   │              │   │              │                 │
│  │ 列式文件:     │   │              │   │              │                 │
│  │ event_type.col│  │              │   │              │                 │
│  │ user_id.col  │   │              │   │              │                 │
│  │ duration.col │   │              │   │              │                 │
│  │ *.idx (索引)  │   │              │   │              │                 │
│  └──────────────┘   └──────────────┘   └──────────────┘                 │
└──────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Query Layer (查询层)                                │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  SQL API     │  │  Grafana     │  │  Superset    │                   │
│  │  (JDBC/ODBC  │  │  (Dashboard) │  │  (BI Tool)   │                   │
│  │   HTTP)      │  │              │  │              │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 数据分区与段 (Segment/Partition)

```
时间分区策略:

┌──────────────────────────────────────────────────────────────────────┐
│  events 表 → PARTITION BY toYYYYMMDD(event_time)                      │
│                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐              │
│  │ Partition: 2024-01-15  │  │ Partition: 2024-01-16  │              │
│  │ (Segments 数据分块)     │  │                        │              │
│  │                        │  │                        │              │
│  │ ┌────────────┐         │  │ ┌────────────┐         │              │
│  │ │ Granule 0  │         │  │ │ Granule 0  │         │              │
│  │ │ (8192 rows)│         │  │ │ (8192 rows)│         │              │
│  │ ├────────────┤         │  │ ├────────────┤         │              │
│  │ │ Granule 1  │         │  │ │ Granule 1  │         │              │
│  │ │ (8192 rows)│         │  │ │ (8192 rows)│         │              │
│  │ ├────────────┤         │  │ ├────────────┤         │              │
│  │ │ ...        │         │  │ │ ...        │         │              │
│  │ └────────────┘         │  │ └────────────┘         │              │
│  └────────────────────────┘  └────────────────────────┘              │
│                                                                      │
│  Granule = 最小IO单元(默认8192行)                                     │
│  每个Granule有独立的 min/max 索引                                     │
│                                                                      │
│  查询优化: WHERE event_time >= '2024-01-15'                          │
│    → 只扫描 2024-01-15 和 2024-01-16 两个分区                          │
│    → 通过min/max索引, 跳过不相关Granule → 极大减少IO                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. 列式存储与压缩

```
列式存储编码与压缩:

1. 字典编码 (Dictionary Encoding):
   country 列: ["US","US","CN","US","JP","CN","CN",...]
   
   字典:  {"US": 0, "CN": 1, "JP": 2}  (基数很低, 如100个国家)
   编码后: [0, 0, 1, 0, 2, 1, 1, ...]
   压缩比: 10x~100x (对低基数列)

2. Delta 编码:
   event_time 列(排序后): [1001, 1002, 1005, 1007, ...]
   存储差值: [1001, +1, +3, +2, ...]
   压缩比: 5x~10x

3. Run-Length Encoding (RLE):
   event_type 列(排序后): ["click","click","click","view","view",...]
   编码: [(3, "click"), (2, "view"), ...]
   压缩比: 100x+

4. 通用压缩:
   LZ4 (快, 压缩比低): 用于查询性能优先的列
   ZSTD (慢, 压缩比高): 用于存储优先的列

列式压缩汇总:
┌────────────────┬──────────────────────────────────┐
│ 列类型          │ 推荐编码                           │
├────────────────┼──────────────────────────────────┤
│ LowCardinality │ 字典编码 + LZ4                     │
│ 排序后的列      │ Delta编码 + LZ4                   │
│ 布尔/分类列     │ RLE + LZ4                         │
│ 纯文本/JSON    │ ZSTD                              │
└────────────────┴──────────────────────────────────┘
```

### 2. 查询执行流程

```
SQL 查询执行:

SELECT 
    country,
    count(*) AS cnt,
    avg(duration_ms) AS avg_duration
FROM events
WHERE event_type = 'purchase'
  AND event_time >= '2024-01-01'
  AND event_time < '2024-01-15'
GROUP BY country
ORDER BY cnt DESC
LIMIT 10;

执行计划:
┌──────────────────────────────────────────────────────────┐
│ 1. Parser: SQL → AST                                     │
│    解析SQL语法, 生成抽象语法树                              │
│                                                          │
│ 2. Optimizer: AST → 优化后AST                             │
│    ┌──────────────────────────────────────────────┐      │
│    │ 谓词下推 (Predicate Pushdown):                 │      │
│    │   WHERE event_type='purchase'                 │      │
│    │   → 扫描event_type列 → 检查min/max索引         │      │
│    │   → 跳过不包含'purchase'的Granule              │      │
│    │                                               │      │
│    │ 分区裁剪 (Partition Pruning):                 │      │
│    │   WHERE event_time >= '2024-01-01'            │      │
│    │   → 只处理 2024-01-01~2024-01-14 的分区       │      │
│    │                                               │      │
│    │ 列裁剪 (Column Pruning):                      │      │
│    │   SELECT country, duration_ms                │      │
│    │   → 只读取这2列, 跳过其他列                    │      │
│    └──────────────────────────────────────────────┘      │
│                                                          │
│ 3. Execution:                                            │
│    Coordinator 将查询分发到多个 Data Node                    │
│    每个 Data Node 扫描负责的 Segment                         │
│    ┌──────────────────────────────────────────────┐      │
│    │ Data Node 1: scan([2024-01-01 ~ 2024-01-05]) │      │
│    │   → {(US, 1200, 45.2), (CN, 800, 32.1), ...}│      │
│    │                                               │      │
│    │ Data Node 2: scan([2024-01-06 ~ 2024-01-10]) │      │
│    │   → {(US, 1100, 46.8), (CN, 750, 31.5), ...}│      │
│    │                                               │      │
│    │ Coordinator: Merge & Aggregate                │      │
│    │   → {(US, 2300, 46.0), (CN, 1550, 31.8), ...}│      │
│    └──────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

### 3. 预聚合（Pre-Aggregation / Materialized View）

```sql
-- ClickHouse 物化视图: 预聚合
-- 创建目标表 (存储聚合结果)
CREATE TABLE events_hourly_agg (
    event_hour  DateTime,
    event_type  LowCardinality(String),
    country     LowCardinality(String),
    cnt         UInt64,
    sum_duration UInt64,
    user_count  UInt64  -- 近似去重(HyperLogLog)
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMMDD(event_hour)
ORDER BY (event_type, country, event_hour);

-- 创建物化视图
CREATE MATERIALIZED VIEW events_hourly_mv
TO events_hourly_agg
AS SELECT
    toStartOfHour(event_time) AS event_hour,
    event_type,
    country,
    count() AS cnt,
    sum(duration_ms) AS sum_duration,
    uniqState(user_id) AS user_count  -- HyperLogLog State
FROM events
GROUP BY event_hour, event_type, country;

-- 查询时利用物化视图 (自动路由)
-- 原始查询可能扫描100亿行 → 物化视图只扫描预聚合的100万行 → 10000x加速
SELECT country, sum(cnt) as total
FROM events_hourly_agg
WHERE event_type = 'purchase' AND event_hour >= '2024-01-01'
GROUP BY country
ORDER BY total DESC
LIMIT 10;

-- Druid 预聚合 (Rollup) 示意
{
  "dataSchema": {
    "dataSource": "events",
    "granularitySpec": {
      "segmentGranularity": "DAY",
      "queryGranularity": "HOUR",
      "rollup": true
    },
    "metricsSpec": [
      {"type": "count", "name": "cnt"},
      {"type": "longSum", "name": "total_duration", "fieldName": "duration_ms"},
      {"type": "hyperUnique", "name": "unique_users", "fieldName": "user_id"}
    ],
    "dimensionsSpec": {
      "dimensions": ["event_type", "country", "device_type"]
    }
  }
}
```

### 4. 近似查询算法

```
大数据实时分析的利器: 近似算法

┌─────────────────────┬──────────┬──────────┬───────────────────────────┐
│ 算法                 │ 精确度    │ 内存     │ 适用                       │
├─────────────────────┼──────────┼──────────┼───────────────────────────┤
│ HyperLogLog         │ ~2% error│ ~1.5KB   │ COUNT(DISTINCT user_id)   │
│ (uniqCombined)      │          │          │                           │
├─────────────────────┼──────────┼──────────┼───────────────────────────┤
│ T-Digest            │ ~1% error│ ~10KB    │ P50/P95/P99              │
│ (quantiles)         │          │          │                           │
├─────────────────────┼──────────┼──────────┼───────────────────────────┤
│ Bloom Filter        │ false pos│ ~1KB     │ 判断某值是否在集合中        │
│                     │ 1%       │          │                           │
├─────────────────────┼──────────┼──────────┼───────────────────────────┤
│ DataSketches        │ config   │ config   │ 通用(Theta Sketch, HLL)   │
└─────────────────────┴──────────┴──────────┴───────────────────────────┘

-- ClickHouse 近似查询:
SELECT 
    uniqCombined(user_id) AS approx_uv,      -- HyperLogLog: ~2% error
    quantiles(0.50, 0.95, 0.99)(duration_ms) AS pcts  -- T-Digest
FROM events WHERE event_time >= '2024-01-01';

-- 精确查询对比:
SELECT count(DISTINCT user_id) AS exact_uv   -- 需要大量内存
FROM events WHERE event_time >= '2024-01-01';
```

### 5. 查询缓存

```
查询缓存策略:

L1: 查询结果缓存 (Query Result Cache)
  Key: hash(query_text)
  Value: 查询结果
  TTL: 60s (实时数据短TTL) / 1h (历史数据)
  存储在: Redis / 内置内存缓存
  Invalidation: 新数据写入时清除相关缓存key

L2: 中间结果缓存 (Segment Cache)
  缓存每个Segment的预计算结果
  当多个查询访问相同Segment时复用

L3: OS Page Cache
  热数据在内存中，减少磁盘IO
  设置: use_uncompressed_cache = true
```

### 6. 实时摄入 (Real-time Ingestion)

```
Kafka → ClickHouse 实时摄入:

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│ Kafka Topic (events)                                                 │
│   │                                                                  │
│   ▼                                                                  │
│ ┌──────────────────────────────────────────────────┐                │
│ │ ClickHouse Kafka Engine (或 Druid Kafka Indexing)│                │
│ │                                                  │                │
│ │ CREATE TABLE events_queue (                      │                │
│ │     event_time DateTime,                         │                │
│ │     event_type String,                           │                │
│ │     user_id UInt64,                              │                │
│ │     ...                                          │                │
│ │ )                                                │                │
│ │ ENGINE = Kafka                                   │                │
│ │ SETTINGS kafka_broker_list = '...',             │                │
│ │         kafka_topic_list = 'events',             │                │
│ │         kafka_group_name = 'ch_consumer',       │                │
│ │         kafka_format = 'JSONEachRow';            │                │
│ │                                                  │                │
│ │ -- Materialized View: 消费Kafka → 写入MergeTree  │                │
│ │ CREATE MATERIALIZED VIEW events_consumer TO events│               │
│ │ AS SELECT * FROM events_queue;                   │                │
│ └──────────────────────────────────────────────────┘                │
│      │                                                               │
│      ▼                                                               │
│ ┌──────────────────────────────────────────────────┐                │
│ │ events (MergeTree)                                │                │
│ │ 数据从Kafka自动流入 → 后台Merge/Parts合并          │                │
│ │ 查询时同时扫描内存中的Part和磁盘中的Part           │                │
│ └──────────────────────────────────────────────────┘                │
│                                                                      │
│  实时 vs 批量摄入:                                                    │
│  ┌──────────────┬──────────────┬──────────────┐                      │
│  │   模式         │   延迟       │   一致性      │                      │
│  ├──────────────┼──────────────┼──────────────┤                      │
│  │ Kafka Engine  │ < 1s        │ At-Least-Once│                      │
│  │ Kafka Connect │ < 10s       │ Exactly-Once │                      │
│  │ Batch Import  │ 分钟~小时    │ Exactly-Once │                      │
│  └──────────────┴──────────────┴──────────────┘                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 扩展性与高可用

### 1. 集群架构

```
ClickHouse/Druid 集群:

                    ┌─────────────────┐
                    │  Load Balancer   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Coordinator   │
                    │ (Query Router)  │
                    │ + Metadata Store│ (ZooKeeper/etcd)
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │ Shard 0  │        │ Shard 1  │        │ Shard 2  │
  │          │        │          │        │          │
  │ Replica 0│        │ Replica 0│        │ Replica 0│
  │ Replica 1│        │ Replica 1│        │ Replica 1│
  └──────────┘        └──────────┘        └──────────┘

  分片策略:
    - 按时间分片: Shard 0 = 2024-01, Shard 1 = 2024-02, ...
    - 按哈希分片: Shard = hash(city) % N
    - 组合: partition by time + distribute by hash

  Replication (ZooKeeper协调):
    - 每个 Shard 有 2-3 个 Replica
    - 写入 Leader Replica → 同步到 Follower Replicas
    - 读从任意 Replica (最终一致性)
```

### 2. 故障恢复

```
故障处理:

┌──────────────────────────────────────────────────────────────┐
│ Data Node 宕机:                                               │
│   该节点的Segment在其他Replica上仍有副本                        │
│   Coordinator 检测到节点不可用 → 路由到其他 Replica             │
│   节点恢复后 → ZooKeeper通知 → Coordinator重新加入路由表      │
│                                                              │
│ Coordinator 宕机:                                              │
│   多Coordinator部署, 无状态                                    │
│   LB自动摘除故障节点 → 路由到其他Coordinator                   │
│                                                              │
│ ZooKeeper 故障:                                               │
│   ZK集群3/5节点, 容忍少数故障                                  │
│   ZK故障期间: 已运行的查询不受影响(Coordinator路由表缓存在内存) │
│   新节点注册/新表创建不可用                                    │
│                                                              │
│ 磁盘故障:                                                      │
│   副本自动修复: 健康副本复制到新节点                            │
└──────────────────────────────────────────────────────────────┘
```

### 3. 数据查询路由 (Segment Routing)

```
Broker/Tier 查询路由:

                              查询请求
                                 │
                                 ▼
                         ┌──────────────┐
                         │  Broker/Router│
                         │              │
                         │ 检查路由表:   │
                         │ 2024-01-01~   │
                         │ 2024-01-05    │
                         │   → Shard0   │
                         └──────┬───────┘
                                │
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │Segment  │ │Segment  │ │Segment  │
              │Pre-Cache│ │SSD Layer│ │HDD Layer│
              │(内存)    │ │(热数据) │ │(温数据) │
              └─────────┘ └─────────┘ └─────────┘

Hot/Warm/Cold 分层存储:
  - Hot (最近1天): 全部在内存, 查询延迟 < 100ms
  - Warm (2~7天): SSD, 查询延迟 < 1s
  - Cold (7~30天): HDD, 查询延迟 ~10s
  - Deep Archive (30天+): S3, 查询延迟分钟级(预加载)
```

### 4. 资源隔离

```
多租户资源隔离:

┌──────────────────────────────────────────────────────────────┐
│ 查询并发限制:                                                  │
│   max_concurrent_queries = 100                               │
│   max_threads = CPU核数                                       │
│                                                              │
│ 内存限制:                                                     │
│   max_memory_usage = RAM的80%                                 │
│   max_memory_usage_for_user = 10GB (单查询上限)               │
│   超限 → 查询被kill (防止一个查询拖垮整个集群)                   │
│                                                              │
│ 查询优先级:                                                   │
│   高优先级: 仪表板查询 (低延迟要求)                             │
│   中优先级: 交互式查询                                          │
│   低优先级: ETL/后台任务                                        │
│                                                              │
│  实现: 资源组 (Resource Groups)                              │
│    SELECT * FROM events                                     │
│    SETTINGS resource_group = 'dashboard';  // 高优先级        │
└──────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 存储 | 列式存储 (Columnar) + 高压缩比 (10x~100x) |
| 索引 | 稀疏索引 (Granularity 8192) + 分区裁剪 |
| 查询 | MPP(大规模并行处理) + 向量化执行(SIMD) |
| 预聚合 | Materialized View / Rollup 预计算 |
| 近似 | HyperLogLog(去重) + T-Digest(分位数) |
| 实时 | Kafka Engine 秒级摄入 |
| 分层 | Hot(内存) → Warm(SSD) → Cold(HDD) → Archive(S3) |
| 高可用 | 副本复制 + Replica Aware 路由 |

**CAP 取舍：** OLAP引擎选择 AP 系统。读路径：副本间是最终一致性（一个副本可能有短暂延迟）。写路径：通常为最终一致性（实时摄入的Part先内存，后异步写入磁盘，合并前可能有短暂数据不一致）。更适合Exactly-Once需求时用Kafka Connect替代Kafka Engine。

**关键技术对比：**

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **ClickHouse** | 通用OLAP,内部用 | 单表查询极快,SQL完善,运维简单 | 无自动数据均衡,JION较弱 |
| **Druid** | 时序+多维分析 | 预聚合优秀,自动均衡,实时摄入 | 架构重,SQL支持弱 |
| **Pinot** | LinkedIn方案 | 类似Druid,对Uber/LinkedIn优 | 社区较小 |
| **StarRocks** | MPP数据库 | 向量化极快,MySQL协议兼容 | 较新,生态待完善 |
