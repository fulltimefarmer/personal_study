# 设计广告点击聚合器 (Design Ad Click Aggregator)

## 题目

设计一个广告点击聚合系统，类似 Google Ads / Facebook Ads，实时统计广告的曝光、点击、转化数据，支持多维度聚合和实时报表。

## 需求澄清

### 功能性需求

1. **实时统计**: 广告的曝光(impression)、点击(click)、转化(conversion)按分钟/小时/天聚合
2. **多维度聚合**: campaign_id, ad_group_id, ad_id, region, device, platform, placement
3. **实时计费**: 按点击计费(CPC)、按千次曝光计费(CPM)、按转化计费(CPA)
4. **预算控制**: 广告预算消耗监控，超额预警/暂停
5. **反作弊检测**: 过滤无效点击 (IVT - Invalid Traffic)
6. **查询支持**: 最近24小时(实时)、最近90天(历史)
7. **数据回填**: 延迟到达的数据需要正确回填聚合

### 非功能性需求

- **高吞吐**: 支持每秒百万级事件 (impression + click + conversion)
- **低延迟**: 实时数据可查延迟 < 10秒
- **准确率**: 计费数据 100% 准确 (exactly-once 语义)
- **持久性**: 数据零丢失
- **高可用**: 99.99%，计费系统不可中断
- **可扩展**: 广告主和流量可能增长10倍

### 容量估算

```
假设:
- DAU: 5亿
- 平均每人每天看到50条广告
- 点击率(CTR): 1%
- 转化率(CVR): 2%

每秒事件计算:
- 峰值QPS = 5亿 × 50条广告 / 86400 × 5(高峰因子) ≈ 145万 events/sec
- 曝光: ~144万/秒 (99%)
- 点击: ~14,400/秒 (1%)
- 转化: ~288/秒 (0.02%)

存储估算:
- 原始事件: 每天 = 145万 × 86400 ≈ 1250亿 events/天
  - 每条event ~200 bytes → 1250亿 × 200 ≈ 25 TB/天
  - 保留7天原始 → 175 TB (Kafka)
- 聚合数据:
  - 维度基数: 10个campaign × 1000 ad_group × 100 ad / ad_group
    × 50（地区）× 3（设备）× 5（平台）× 10（位置）
    ≈ 7500万 combinations → 实际活跃~1000万
  - 每分钟聚合: 1000万 × 4 bytes × 3 metrics ≈ 120 MB/min
  - 每天: 120 MB × 1440 ≈ 170 GB
  - 90天: 15 TB

实时查询 QPS: ~10,000（dashboard 刷新 + 广告主查询）
```

## API设计

### 事件上报 API

```protobuf
// 广告事件上报 (客户端 → 聚合系统)
// POST /api/v1/events (批量)
// Content-Type: application/x-protobuf 或 application/json

message AdEventBatch {
  repeated AdEvent events = 1;
  int64 batch_timestamp_ms = 2;
  string request_id = 3;             // 幂等去重
  string source = 4;                 // "android_sdk", "ios_sdk", "web_pixel"
}

message AdEvent {
  string event_id = 1;               // 全局唯一事件ID
  string event_type = 2;             // "impression", "click", "conversion"
  int64 event_timestamp_ms = 3;      // 事件发生时间 (客户端时间)

  // 广告层级标识
  string campaign_id = 4;
  string ad_group_id = 5;
  string ad_id = 6;
  string creative_id = 7;

  // 流量侧标识
  string publisher_id = 8;
  string placement_id = 9;
  string app_id = 10;

  // 用户/设备信息
  string user_id = 11;
  string device_id = 12;             // IDFA/GAID
  string ip_address = 13;            // 用于地域推断
  string user_agent = 14;

  // 上下文
  string region = 15;
  string device_type = 16;           // "mobile", "tablet", "desktop"
  string os = 17;                    // "ios", "android", "web"
  string connection_type = 18;       // "wifi", "4g", "5g"

  // 计费相关
  double bid_amount = 19;            // 竞价价格 (CPC/CPM bid)
  string currency = 20;              // "USD", "CNY"

  // 扩展属性
  map<string, string> extra = 21;
}
```

### 查询 API

```protobuf
// 广告数据查询 API
// GET /api/v1/report?start_time=X&end_time=Y&metrics=Z&dimensions=W&filters=V

message ReportRequest {
  int64 start_time_ms = 1;
  int64 end_time_ms = 2;
  repeated string metrics = 3;       // ["impressions","clicks","ctr","cost","cvr"]
  repeated string dimensions = 4;    // ["campaign_id","ad_id","region","hour"]
  repeated Filter filters = 5;
  string granularity = 6;            // "minute", "hour", "day"
  repeated SortBy sort = 7;
  int32 limit = 8 [default = 100];
  int32 offset = 9;
}

message Filter {
  string field = 1;
  string operator = 2;               // "=", "IN", ">", "<", "BETWEEN"
  repeated string values = 3;
}

message ReportResponse {
  repeated ReportRow rows = 1;
  ReportSummary summary = 2;
  string generated_at = 3;
}

message ReportRow {
  map<string, string> dimension_values = 1;  // {"campaign_id":"123","region":"US"}
  map<string, double> metric_values = 2;     // {"impressions":1000,"clicks":50}
}

message ReportSummary {
  map<string, double> totals = 1;
}

// 预算查询
// GET /api/v1/campaign/{campaign_id}/budget
message BudgetStatus {
  string campaign_id = 1;
  double daily_budget = 2;
  double daily_spent = 3;
  double total_budget = 4;
  double total_spent = 5;
  string status = 6;                 // "active", "paused", "budget_exhausted"
}
```

## 数据模型

### 聚合数据存储方案

```
┌────────────────────────────────────────────────────────────────┐
│              Lambda 架构: 实时 + 批处理                          │
│                                                                │
│  实时层 (Speed Layer):                                          │
│  ─────────────────────────────                                  │
│  Kafka → Flink/Spark Streaming → OLAP Store (Druid/ClickHouse)  │
│  延迟: < 10秒                                                   │
│  保留: 最近24-48小时                                            │
│                                                                │
│  批处理层 (Batch Layer):                                        │
│  ─────────────────────────────                                  │
│  S3/HDFS → Spark Batch → OLAP Merge                             │
│  延迟: T+1 (每天一次)                                           │
│  保留: 90天+                                                   │
│                                                                │
│  服务层 (Serving Layer):                                        │
│  ─────────────────────────────                                  │
│  Query Router → Druid/ClickHouse (实时+历史)                     │
│  合并实时和批处理结果                                           │
└────────────────────────────────────────────────────────────────┘
```

### Druid/ClickHouse Schema

```sql
-- ClickHouse 聚合表
CREATE TABLE ad_event_aggregations (
    event_date Date,
    event_hour UInt8,
    event_minute UInt16,
    campaign_id String,
    ad_group_id String,
    ad_id String,
    creative_id String,
    publisher_id String,
    placement_id String,
    region String,
    device_type String,
    os String,
    impressions AggregateFunction(sum, UInt64),
    clicks AggregateFunction(sum, UInt64),
    conversions AggregateFunction(sum, UInt64),
    cost AggregateFunction(sum, Float64),
    revenue AggregateFunction(sum, Float64),
    click_uu AggregateFunction(uniq, String),
    imp_uu AggregateFunction(uniq, String)
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, campaign_id, ad_id, region, device_type, event_hour)
TTL event_date + INTERVAL 90 DAY DELETE
SETTINGS index_granularity = 8192;
```

### 原始事件 Schema (Hive/Iceberg - 批处理用)

```sql
CREATE TABLE ad_events_raw (
    event_id STRING,
    event_type STRING,
    event_timestamp_ms BIGINT,
    processed_at_ms BIGINT,
    -- 广告层级
    campaign_id STRING,
    ad_group_id STRING,
    ad_id STRING,
    creative_id STRING,
    -- 流量
    publisher_id STRING,
    placement_id STRING,
    app_id STRING,
    -- 用户/设备
    user_id STRING,
    device_id STRING,
    ip_address STRING,
    -- 上下文
    region STRING,
    device_type STRING,
    os STRING,
    connection_type STRING,
    -- 计费
    bid_amount DOUBLE,
    currency STRING,
    final_cost DOUBLE,
    -- 标记
    is_valid BOOLEAN,                   -- 反作弊标记
    fraud_type STRING,                  -- 作弊类型
    -- 分区
    dt STRING
)
PARTITIONED BY (dt STRING)
STORED AS PARQUET;
```

### 预算/计费表

```sql
-- 计费表 (MySQL/PostgreSQL - 强一致性, 计算金额)
CREATE TABLE ad_budget (
    campaign_id VARCHAR(64) PRIMARY KEY,
    advertiser_id VARCHAR(64) NOT NULL,
    daily_budget DECIMAL(12,2) NOT NULL,
    total_budget DECIMAL(14,2) NOT NULL,
    bid_type ENUM('CPC', 'CPM', 'CPA', 'CPCV') NOT NULL,
    bid_amount DECIMAL(10,4) NOT NULL,
    status ENUM('active', 'paused', 'completed', 'budget_exhausted') DEFAULT 'active',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE daily_spending (
    campaign_id VARCHAR(64) NOT NULL,
    spend_date DATE NOT NULL,
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions BIGINT DEFAULT 0,
    cost DECIMAL(12,2) DEFAULT 0.00,
    PRIMARY KEY (campaign_id, spend_date)
);
```

## 高层次架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         广告点击聚合系统架构                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      数据采集层 (Data Ingestion)                    │  │
│  │                                                                    │  │
│  │  SDK(客户端) ──► CDN Edge ──► Events API ──► Kafka (原始事件)      │  │
│  │  Server端 ──► 直接写 Kafka                                        │  │
│  │  Conversion Pixel ──► Events API                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    实时处理层 (Stream Processing)                   │  │
│  │                                                                    │  │
│  │  ┌───────────────┐  ┌──────────────────┐  ┌─────────────────┐    │  │
│  │  │ 反作弊过滤器    │  │ 预聚合引擎        │  │ 预算控制器       │    │  │
│  │  │ Bot detection │  │ Flink Aggregator │  │ Budget Monitor  │    │  │
│  │  │ IP黑白名单     │  │ (1min窗口聚合)   │  │ (超预算停投)     │    │  │
│  │  │ 频率检测      │  │                  │  │                 │    │  │
│  │  └───────┬───────┘  └────────┬─────────┘  └────────┬────────┘    │  │
│  │          │                  │                       │             │  │
│  │          └──────────────────┼───────────────────────┘             │  │
│  │                             │                                     │  │
│  └─────────────────────────────┼─────────────────────────────────────┘  │
│                                │                                        │
│              ┌─────────────────┼─────────────────┐                      │
│              ▼                 ▼                 ▼                      │
│  ┌───────────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │ 实时OLAP Store     │ │ 预算Cache    │ │ 计费系统      │               │
│  │ (Druid/ClickHouse)│ │ (Redis)      │ │ (MySQL+MQ)   │               │
│  │ 最近24h分钟级数据  │ │ 实时消耗缓存  │ │ 账单/对账     │               │
│  └───────────────────┘ └──────────────┘ └──────────────┘               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    批处理层 (Batch Processing) - Lambda 校正       │  │
│  │                                                                    │  │
│  │  S3/HDFS ──► Spark Batch ──► 重新聚合 ──► 校正 OLAP Store         │  │
│  │  (每小时执行一次 T+1h 数据回填)                                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      查询服务层 (Query Service)                     │  │
│  │                                                                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐   │  │
│  │  │ 实时查询路由     │  │ 缓存层(RD+本地) │  │ 预算API+Alerting │   │  │
│  │  │ (近24h用RT,     │  │ 热门查询缓存    │  │ 超预算自动暂停    │   │  │
│  │  │  历史用Batch)   │  │ TTL: 1-5min     │  │ 通知广告主        │   │  │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 事件采集与数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        事件采集优先级设计                                │
│                                                                         │
│  Impression (曝光) vs Click (点击) 处理优先级分离:                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        曝 光 通 道                                 │  │
│  │  ┌──────────┐    ┌───────────┐    ┌──────────────────┐            │  │
│  │  │ 客户端SDK │───►│ Edge      │───►│ Kafka            │            │  │
│  │  │ (采样日志) │    │ Collector │    │ (high_volume_tp) │            │  │
│  │  └──────────┘    └───────────┘    └────────┬─────────┘            │  │
│  │                                            │                       │  │
│  │  曝光可采样 (例如1% 抽样记录单个曝光):          ▼                       │  │
│  │  - 统计计数用计数器(聚合)，不需要每条原始日志    │                       │  │
│  │  - Billing统计依赖采样+估算                     │                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        点 击 通 道 (全量不采样)                     │  │
│  │  ┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌────────┐ │  │
│  │  │ 客户端    │───►│ Click     │───►│ Kafka         │───►│Flink   │ │  │
│  │  │ (302跳转) │    │ Collector │    │(click_topic)  │    │(计费)  │ │  │
│  │  └──────────┘    └───────────┘    └──────────────┘    └────────┘ │  │
│  │                                                                   │  │
│  │  点击必须全量记录:                                                 │  │
│  │  - CPC计费 = 点击数 × bid_price                                   │  │
│  │  - 每条点击都影响计费金额，不可丢失，不可重复                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心深入

### 1. Exactly-Once 语义保证

```
┌────────────────────────────────────────────────────────────────┐
│               Exactly-Once 处理保证                            │
│                                                                │
│  问题: 分布式系统中消息可能被重复消费导致计费重复                   │
│                                                                │
│  方案一: 事件去重 (Idempotent Events)                          │
│  ────────────────────────────────────────────────              │
│  每个事件携带全局唯一 ID (event_id = UUID)                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Flink 处理:                                             │   │
│  │                                                         │   │
│  │ source.flatMap(event => {                                │   │
│  │   if (!dedupFilter.seen(event.event_id)) {              │   │
│  │     dedupFilter.mark(event.event_id)                    │   │
│  │     emit(event)                                         │   │
│  │   }                                                     │   │
│  │ })                                                      │   │
│  │                                                         │   │
│  │ dedupFilter = new BloomFilter(1_000_000_000, 0.01)     │   │
│  │ // 10亿容量, 1% 误判率 (宁可少扣不重复)                   │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  方案二: 幂等写入 (Idempotent Sink)                             │
│  ────────────────────────────────────────────────              │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ INSERT INTO daily_spending (campaign_id, clicks, cost)  │   │
│  │ VALUES ('camp_123', :clicks, :cost)                     │   │
│  │ ON DUPLICATE KEY UPDATE                                 │   │
│  │   clicks = VALUES(clicks),                              │   │
│  │   cost = VALUES(cost),                                  │   │
│  │ WHERE event_batch_id NOT IN processed_batches           │   │
│  │                                                         │   │
│  │ 关键: 两阶段提交 (2PC) + Checkpoint                         │   │
│  │   1. Flink Checkpoint 触发                                  │   │
│  │   2. Sink 完成写入                             │   │
│  │   3. 提交 Kafka Offset → 标记已处理               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  方案三: 端到端 Exactly-Once                                   │
│  ────────────────────────────────────────────────              │
│  Kafka Transactions + Flink TwoPhaseCommitSink          │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Flink Job:                                              │   │
│  │  env.enableCheckpointing(60000)                         │   │
│  │  source = KafkaConsumer("events",                      │   │
│  │     isolation.level=read_committed)                     │   │
│  │                                                         │   │
│  │  stream.addSink(new TwoPhaseCommitSink {                │   │
│  │    beginTransaction() → 开始事务                 │   │
│  │    invoke(value, context) → 写入目标           │   │
│  │    preCommit() → flush/prepare                   │   │
│  │    commit() → 最终提交                         │   │
│  │    abort() → 回滚事务                         │   │
│  │  })                                                    │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 2. 反作弊检测 (Fraud Detection)

```
┌────────────────────────────────────────────────────────────────┐
│                      反作弊检测架构                              │
│                                                                │
│  多层次过滤:                                                    │
│                                                                │
│  第一层: 客户端侧 (SDK)                                         │
│  ────────────────────────────────────────────────              │
│  - Device Fingerprint 采集 (Canvas, WebGL, AudioContext)       │
│  - 点击位置验证 (是否在广告区域内)                                │
│  - Viewability 验证 (广告是否在可视区域超过1秒)                   │
│  - Challenge-Response (CAPTCHA for high-value ads)            │
│                                                                │
│  第二层: 规则引擎 (实时)                                         │
│  ────────────────────────────────────────────────              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 规则:                                                      │ │
│  │ 1. IP 黑名单/白名单                                        │ │
│  │ 2. 频率限制: 同一 device_id 每分钟 > 1000 次点击 → 拦截     │ │
│  │ 3. 点击间隔: 相邻点击间隔 < 10ms → 机器人                    │ │
│  │ 4. 曝光/点击比: CTR > 50% → 异常                           │ │
│  │ 5. User Agent 一致性检查                                    │ │
│  │ 6. Referrer 校验 (点击来源)                                  │ │
│  │ 7. 地理位置/IP 一致性                                        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                │
│  第三层: ML 模型 (准实时)                                        │
│  ────────────────────────────────────────────────              │
│  - 行为序列建模: LSTM/Transformer 判断点击序列是否自然            │
│  - 特征: 点击时间间隔分布, 鼠标轨迹, 页面停留时长, 设备特征         │
│  - 判断结果异步标记 is_valid, 后续计费排除无效点击                 │
│                                                                │
│  第四层: 离线审计 (T+1)                                         │
│  ────────────────────────────────────────────────              │
│  - 全量数据回溯分析                                              │
│  - 已知Bot IP库更新                                             │
│  - 广告主申诉处理 (refund)                                       │
└────────────────────────────────────────────────────────────────┘
```

### 3. 实时聚合方案对比

```
┌─────────────────────────────────────────────────────────────────┐
│               实时 OLAP 引擎对比                                  │
│                                                                 │
│  方案A: Druid                                                    │
│  ─────────────────────────────                                  │
│  优点:                                                           │
│  - Lambda 架构原生支持 (实时摄入 + 批处理替换)                      │
│  - 预聚合 (rollup) 大幅减少存储                                    │
│  - Bitmap 索引加速过滤查询                                        │
│  - 支持精确去重 (Thetasketches for HLL)                           │
│                                                                 │
│  缺点:                                                           │
│  - 运维复杂 (多组件: Coordinator, Broker, Historical, MiddleManager)│
│  - 不支持 JOIN (需要数据预关联)                                    │
│  - 导入延迟较高 (分钟级)                                          │
│                                                                 │
│  方案B: ClickHouse                                               │
│  ─────────────────────────────                                   │
│  优点:                                                           │
│  - 超高压缩比 (列存 + 编码)                                        │
│  - SQL兼容，JOIN支持                                              │
│  - 查询性能优秀 (向量化执行)                                      │
│  - 运维简单 (单二进制, 无外部依赖)                                │
│                                                                 │
│  缺点:                                                           │
│  - 不支持流式摄入 (需要 Kafka Engine 或批量导入)                    │
│  - 更新/删除性能较弱 (Mutation)                                    │
│  - 无原生 Lambda 支持                                             │
│                                                                 │
│  方案C: Apache Pinot                                             │
│  ─────────────────────────────                                   │
│  优点:                                                           │
│  - 列式存储 + 倒排/Star-Tree索引                                  │
│  - 亚秒级查询延迟                                                 │
│  - 原生 Upsert 支持                                               │
│  - 被 LinkedIn, Uber 大规模验证                                   │
│                                                                 │
│  最终选型建议: ClickHouse (简单运维 + 高性能)                       │
│  如果已有 Druid/Kafka 生态可考虑 Druid                             │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Lambda 架构的数据校正

```
┌────────────────────────────────────────────────────────────────┐
│              Lambda 架构数据校正流程                              │
│                                                                │
│  为什么需要 Lambda?                                              │
│  - 实时流处理可能出现数据延迟、乱序、drop                           │
│  - 需要批处理重新计算保证最终一致性                                │
│                                                                │
│  校正流程:                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  T0 (实时):                                              │  │
│  │  ┌───────────┐       ┌──────────┐       ┌──────────┐   │  │
│  │  │ Kafka     │──────►│ Flink    │──────►│ Druid/CH │   │  │
│  │  │ (实时流)   │       │ Window Agg│       │ (实时层)  │   │  │
│  │  └───────────┘       └──────────┘       └──────────┘   │  │
│  │                                                          │  │
│  │  T+1h (校正):                                            │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 1. Spark 读取 S3 上 T-2h ~ T-1h 的原始数据       │   │  │
│  │  │ 2. 重新按相同维度聚合                             │   │  │
│  │  │ 3. 对比实时层数据 → 计算差异                      │   │  │
│  │  │ 4. UPSERT 校正数据到实时层                        │   │  │
│  │  │ 5. 如果差异较大(>1%) → 触发告警，调查原因          │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                          │  │
│  │  T+1d (最终校正):                                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ 1. 全量 D-1 数据重新聚合                          │   │  │
│  │  │ 2. 写入历史数据表 (最终版本)                       │   │  │
│  │  │ 3. 计费对账 (billing reconciliation)              │   │  │
│  │  │ 4. 生成广告主报表                                  │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 5. 预算控制与超投保护

```
┌────────────────────────────────────────────────────────────────┐
│                    预算控制机制                                  │
│                                                                │
│  挑战: 为什么不能即时停止?                                       │
│  - 竞价出价 → 赢得展示 → 用户实际看到广告 → 点击                  │
│  - 预算用尽时已出价但尚未展示的广告 → 超投 (overspend)            │
│                                                                │
│  解决方案:                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  预算消耗追踪 (Redis, 亚秒级更新):                         │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ Key: budget:daily:{campaign_id}:{date}             │  │  │
│  │  │ Type: String                                       │  │  │
│  │  │ Value: {"budget":1000.00, "spent":450.50,          │  │  │
│  │  │         "buffer":100.00, "status":"active"}        │  │  │
│  │  │                                                    │  │  │
│  │  │ 每次点击:                                           │  │  │
│  │  │ INCRBY budget:daily:{id}:{date} 0.5               │  │  │
│  │  │ 如果 GET > budget → status = "paused"              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  平滑消费 (Pacing):                                       │  │
│  │  - 日预算1000元 → 每小时约41.67元                         │  │
│  │  - 实际流量不均 → 前1小时就用掉500元 → 降低出价/暂停     │  │
│  │  - Pacing算法: 实时计算预算消耗速率，动态调整投放速率       │  │
│  │                                                          │  │
│  │  预算缓冲 (Buffer/Overdelivery):                          │  │
│  │  - 允许5-10% 超投 → 实际预算1100元 → 标记暂停             │  │
│  │  - 广告平台通常承担超投成本作为商业让步                      │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  预算暂停通知流程:                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  budget_spent >= budget_threshold                          │  │
│  │     │                                                      │  │
│  │     ▼                                                      │  │
│  │  ┌─────────────────┐                                       │  │
│  │  │ 暂停campaign     │                                       │  │
│  │  │ (更新状态为       │                                       │  │
│  │  │  budget_exhausted│                                       │  │
│  │  └────────┬────────┘                                       │  │
│  │           │                                                │  │
│  │           ▼                                                │  │
│  │  ┌─────────────────┐    ┌──────────────┐                   │  │
│  │  │ 通知Ad Server    │───►│ Ad Server     │                   │  │
│  │  │ (远程调用)       │    │ 停止该campaign│                   │  │
│  │  └────────┬────────┘    │ 的出价       │                   │  │
│  │           │             └──────────────┘                   │  │
│  │           ▼                                                │  │
│  │  ┌─────────────────┐                                       │  │
│  │  │ 通知广告主       │                                       │  │
│  │  │ (Email/API       │                                       │  │
│  │  │  Callback/SMS)  │                                       │  │
│  │  └─────────────────┘                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 存储分片策略

```
┌──────────────────────────────────────────────────────────────┐
│                    存储层水平扩展                              │
│                                                              │
│  Kafka 分区策略:                                              │
│  - 按 campaign_id hash → 同一广告事件进入同一分区             │
│  - 分区数 = 目标吞吐量 / 单分区吞吐量(50MB/s)                 │
│  - 145万 events/sec × 200bytes → 290 MB/s → ~6个分区        │
│  - 实际配置: 32个分区 (考虑峰值10x)                           │
│                                                              │
│  OLAP 分片 (ClickHouse Cluster):                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │  Shard 1              Shard 2              Shard 3    │  │
│  │  ┌──────────┐        ┌──────────┐        ┌──────────┐ │  │
│  │  │ Replica 1│◄─sync──│ Replica 1│◄─sync──│ Replica 1│ │  │
│  │  └──────────┘        └──────────┘        └──────────┘ │  │
│  │  ┌──────────┐        ┌──────────┐        ┌──────────┐ │  │
│  │  │ Replica 2│        │ Replica 2│        │ Replica 2│ │  │
│  │  └──────────┘        └──────────┘        └──────────┘ │  │
│  │                                                       │  │
│  │ 数据分布策略:                                          │  │
│  │ Distributed table → local tables                       │  │
│  │ shard_key = rand() 或 cityHash64(campaign_id)         │  │
│  │ 或按时间分区分布到不同 shard                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  查询路由:                                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ SELECT campaign_id, sum(impressions)                   │  │
│  │ FROM distributed_table                                 │  │
│  │ WHERE date BETWEEN '2024-01-01' AND '2024-01-07'      │  │
│  │ GROUP BY campaign_id                                   │  │
│  │                                                       │  │
│  │ → Distributed engine 自动将查询分发到所有 Shard        │  │
│  │ → 各 Shard 返回 local 结果 → merged on initiator       │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 故障恢复

```
┌──────────────────────────────────────────────────────────────┐
│                    容错与故障恢复                              │
│                                                              │
│  1. Flink 容错:                                               │
│     - Checkpoint (exactly-once state备份)                     │
│     - 故障自动从最近 checkpoint 恢复                           │
│     - Savepoint 支持计划性维护/升级                            │
│                                                              │
│  2. Kafka 容错:                                               │
│     - 多broker, 多副本, 生产端 ack=all                       │
│     - 数据保留7天，Flink故障恢复后可重放                       │
│                                                              │
│  3. OLAP 容错:                                                │
│     - 每 Shard 至少2副本                                      │
│     - 读写分离 (writer → 主, reader → 副本)                   │
│                                                              │
│  4. 预算Cache容错:                                            │
│     - Redis Sentinel / Cluster                                │
│     - Cache miss 时 fallback 到 MySQL                         │
│                                                              │
│  5. 计费容错:                                                 │
│     - 计费记录双写 (OLAP + MySQL)                              │
│     - 每日对账: OLAP聚合 vs MySQL计费记录                      │
│     - 不一致 → 自动修正 + 告警                                │
│                                                              │
│  6. 可观测性:                                                 │
│     - 端到端事件延迟监控 (客户端→Kafka→Flink→OLAP)           │
│     - Exactly-Once 成功率监控                                 │
│     - 反作弊拦截率监控                                         │
│     - 计费准确性 dashboard                                     │
│     - 每日自动对账报告                                         │
└──────────────────────────────────────────────────────────────┘
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 消息队列 | Kafka | 高吞吐 + 持久化 + 多消费者 |
| 流计算 | Flink | Exactly-Once + 原生窗口聚合 |
| 实时OLAP | ClickHouse | 高压缩比 + SQL友好 + 运维简单 |
| 批处理 | Spark (S3/Hive) | 数据校正 + 历史数据 |
| 去重 | Bloom Filter + 事件ID | 低内存 + 低误判 |
| 反作弊 | 规则引擎 + ML模型 | 实时拦截 + 异步分析 |
| 预算控制 | Redis + 异步通知 | 亚秒级预算检查 |
| 计费 | MySQL (事务保证) | ACID + 对账 |
| 架构 | Lambda (实时+批处理) | 兼顾延迟和准确性 |

核心设计要点:
1. **Exactly-Once 是核心**: 计费数据必须精确，使用事件唯一ID + BloomFilter + 两阶段提交
2. **Lambda 架构弥补流处理缺陷**: 批处理周期校正数据，保证最终一致性
3. **预算控制需要异步通知机制**: 实时消费追踪 + 超预算自动暂停Ad Server
4. **反作弊多层次防御**: 客户端 → 规则引擎 → ML模型 → 离线审计
5. **曝光可采样，点击必须全量**: 计费精度要求点击每条必达
6. **每日对账**: OLAP聚合数据和MySQL计费记录对齐，保证财务准确
