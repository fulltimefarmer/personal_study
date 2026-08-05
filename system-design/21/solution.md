# 设计指标监控与告警系统 (Design Metrics Monitoring & Alerting System)

## 题目

设计一个类似 Prometheus + Grafana 的指标监控与告警系统，支持大规模分布式系统的指标采集、存储、查询和告警。

## 需求澄清

### 功能性需求

1. **指标采集 (Metrics Collection)**: 支持多种方式采集指标，包括 Pull 模式（主动拉取）和 Push 模式（主动推送）
2. **指标类型支持**: Counter（计数器）、Gauge（瞬时值）、Histogram（直方图）、Summary（摘要）
3. **标签系统 (Label/Tag)**: 支持多维标签，如 `{method="GET", endpoint="/api/users", status="200"}`
4. **查询语言 (Query Language)**: 支持 PromQL 类似的查询语言，可以聚合、过滤、计算速率等
5. **告警规则 (Alerting Rules)**: 用户定义告警规则，条件触发后发送通知
6. **通知渠道**: 支持 Email、Slack、PagerDuty、Webhook 等
7. **仪表盘 (Dashboard)**: 可视化展示指标趋势图、热力图等
8. **数据保留策略 (Retention)**: 支持自动过期删除旧数据
9. **多租户 (Multi-tenancy)**: 支持不同团队/项目的数据隔离

### 非功能性需求

- **高可用**: 99.99% 可用性，监控系统自身不能成为单点故障
- **低延迟写入**: 写入延迟 < 10ms (p99)
- **高吞吐**: 支持每秒百万级指标数据点写入
- **水平扩展**: 存储和查询层均需水平扩展
- **存储效率**: 高效的时序数据压缩
- **查询性能**: 复杂聚合查询秒级返回

### 容量估算

假设监控1000台服务器，每个服务器暴露200个指标，每15秒采集一次：

```
数据点数量计算:
- 总指标数 = 1000 × 200 = 200,000 个指标
- 每秒写入数据点 = 200,000 / 15 ≈ 13,333 数据点/秒
- 每天数据点 ≈ 13,333 × 86,400 ≈ 1.15 亿数据点/天

考虑标签的基数膨胀（每个指标5个标签组合）:
- 实际数据点 ≈ 13,333 × 5 ≈ 66,665 数据点/秒
- 每天 ≈ 57.6 亿数据点

存储估算:
- 每个数据点 ≈ 12 bytes（压缩后，含时间戳+值+标签ID）
- 每天存储 ≈ 57.6亿 × 12 ≈ 69 GB/天
- 保留30天 ≈ 2 TB
- 考虑副本(×3) ≈ 6 TB

查询QPS: ~ 100 QPS（仪表盘刷新+告警评估）
```

## API设计

```protobuf
// 指标写入 API
// 对于 Push 模式，提供 HTTP/gRPC 接口
// POST /api/v1/write
message WriteRequest {
  repeated TimeSeries timeseries = 1;
}

message TimeSeries {
  repeated Label labels = 1;          // {name, value}
  repeated Sample samples = 2;        // [{timestamp, value}]
}

message Label {
  string name = 1;
  string value = 2;
}

message Sample {
  int64 timestamp_ms = 1;
  double value = 2;
}

// POST /api/v1/write
// Response: 200 OK / 204 No Content (Prometheus style)
```

```protobuf
// 查询 API
// GET /api/v1/query?query=<PromQL>&time=<timestamp>
// POST /api/v1/query_range?query=<PromQL>&start=<ts>&end=<ts>&step=<duration>
message QueryRequest {
  string query = 1;                   // PromQL 查询语句
  int64 time_ms = 2;                  // 即时查询时间点
  int64 start_ms = 3;                 // 范围查询开始时间
  int64 end_ms = 4;                   // 范围查询结束时间
  string step = 5;                    // 步长，如 "15s", "1m"
  int32 limit = 6;                    // 结果数量限制
}

message QueryResponse {
  string result_type = 1;             // "vector", "matrix", "scalar", "string"
  repeated Result results = 2;
}

message Result {
  map<string, string> metric = 1;     // 标签集合
  repeated Value values = 2;          // 时序值（matrix返回）
  Value value = 3;                    // 单个值（vector返回）
}

message Value {
  int64 timestamp_ms = 1;
  string value = 2;                   // 使用字符串保持精度
}
```

```protobuf
// 告警规则管理 API
// POST /api/v1/rules
// GET /api/v1/rules
// DELETE /api/v1/rules/{rule_id}

message AlertRule {
  string rule_id = 1;
  string name = 2;
  string query = 3;                   // PromQL 查询
  string condition = 4;              // ">", "<", ">=", "<=", "=="
  double threshold = 5;
  string duration = 6;               // 持续时间, 如 "5m"
  map<string, string> labels = 7;    // 告警标签
  map<string, string> annotations = 8; // 告警描述
  repeated AlertChannel channels = 9; // 通知渠道
  AlertSeverity severity = 10;       // "critical", "warning", "info"
}

message AlertChannel {
  string channel_id = 1;
  ChannelType type = 2;              // EMAIL, SLACK, PAGERDUTY, WEBHOOK
  string config = 3;                 // 渠道配置 JSON
}

enum AlertSeverity {
  CRITICAL = 0;
  WARNING = 1;
  INFO = 2;
}

enum ChannelType {
  EMAIL = 0;
  SLACK = 1;
  PAGERDUTY = 2;
  WEBHOOK = 3;
}
```

## 数据模型

### 时序数据存储模型

```
核心数据结构: 倒排索引 (Inverted Index) + 时间序列块

┌─────────────────────────────────────────────────────────┐
│                   内存索引 (Memory Index)                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Labels → Posting List → SeriesID               │    │
│  │ "__name__" → {app="api"} → [series_1, ...]      │    │
│  │ "job" → {job="web"} → [series_2, ...]            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

存储结构设计:
┌──────────────────────────────────────────┐
│           Time-Stamped Chunk              │
│  ┌────────────────────────────────────┐   │
│  │ Series ID (8 bytes)                │   │
│  │ Start Time (8 bytes)               │   │
│  │ End Time (8 bytes)                 │   │
│  │ Chunk Encoding Type (1 byte)       │   │
│  │ ┌──────────────────────────────┐   │   │
│  │ │ Delta-delta of timestamps    │   │   │
│  │ │ XOR of float values          │   │   │
│  │ └──────────────────────────────┘   │   │
│  └────────────────────────────────────┘   │
└──────────────────────────────────────────┘

使用 Facebook Gorilla 的压缩算法:
- Timestamp 压缩: delta-of-delta, 约 1.37 bytes/点
- Value 压缩: XOR, 约 1.37 bytes/点
- 总计每个数据点约 2.74 bytes
```

### SQL Schema (元数据存储 - 告警规则/通知渠道)

```sql
CREATE TABLE alert_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    condition_op VARCHAR(10) NOT NULL,
    threshold DOUBLE NOT NULL,
    duration_seconds INT NOT NULL DEFAULT 300,
    severity ENUM('critical', 'warning', 'info') NOT NULL,
    labels JSON,
    annotations JSON,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enabled (enabled)
);

CREATE TABLE alert_channels (
    channel_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type ENUM('email', 'slack', 'pagerduty', 'webhook') NOT NULL,
    config JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rule_channel_mapping (
    rule_id VARCHAR(64) NOT NULL,
    channel_id VARCHAR(64) NOT NULL,
    PRIMARY KEY (rule_id, channel_id),
    FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES alert_channels(channel_id) ON DELETE CASCADE
);

CREATE TABLE alert_state (
    rule_id VARCHAR(64) NOT NULL,
    fingerprint VARCHAR(255) NOT NULL,  -- label set hash
    state ENUM('pending', 'firing', 'resolved') NOT NULL,
    fired_at TIMESTAMP,
    resolved_at TIMESTAMP,
    last_evaluated_at TIMESTAMP,
    labels JSON,
    PRIMARY KEY (rule_id, fingerprint)
);

CREATE TABLE alert_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_id VARCHAR(64) NOT NULL,
    fingerprint VARCHAR(255) NOT NULL,
    state ENUM('firing', 'resolved') NOT NULL,
    fired_at TIMESTAMP,
    resolved_at TIMESTAMP,
    labels JSON,
    annotations JSON,
    notification_sent BOOLEAN DEFAULT FALSE,
    INDEX idx_rule_id_time (rule_id, fired_at)
);
```

## 高层次架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Dashboard (Grafana-like)                       │
│                         ┌─────────────────────────┐                     │
│                         │     Alert Management    │                     │
│                         └─────────────────────────┘                     │
└────────────┬────────────────────────────────────┬────────────────────────┘
             │                                    │
             ▼                                    ▼
┌─────────────────────────┐          ┌───────────────────────────────┐
│      API Gateway        │          │       Alert Manager            │
│  (Auth / Rate Limit)    │          │  ┌──────────┐  ┌──────────┐   │
└────────────┬────────────┘          │  │  Silencer │  │ Inhibitor│   │
             │                       │  └──────────┘  └──────────┘   │
    ┌────────┼────────┐              │  ┌──────────────────────────┐  │
    ▼        ▼        ▼              │  │  Notification Dispatcher │  │
┌────────┐┌───────┐┌───────┐        │  │  Email/Slack/PagerDuty  │  │
│ Write  ││ Query ││ Rules │        │  └──────────────────────────┘  │
│ Router ││Router ││Engine │        └───────────────┬───────────────┘
└───┬────┘└───┬───┘└───┬───┘                        │
    │         │         │                           ▼
    │         │         │              ┌───────────────────────────┐
    │         │         └──────────────│   Rule Evaluator          │
    │         │                        │  (Periodic Query Executor)│
    │         │                        └───────────────┬───────────┘
    ▼         ▼                                        │
┌────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│  │      Hot Storage (In-Memory)│  │  Time Series Database   │  │
│  │      ┌───────────────────┐  │  │  ┌───────────────────┐  │  │
│  │      │   Inverted Index  │  │  │  │  Compressed Chunks│  │  │
│  │      │  (Label → Series) │  │  │  │  on SSD           │  │  │
│  │      └───────────────────┘  │  │  └───────────────────┘  │  │
│  │      ┌───────────────────┐  │  │  ┌───────────────────┐  │  │
│  │      │   Recent Chunks   │  │  │  │  S3/Blob (Archival│  │  │
│  │      │  (last 2h)        │  │  │  │   >30 days)       │  │  │
│  │      └───────────────────┘  │  │  └───────────────────┘  │  │
│  └─────────────────────────────┘  └─────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│          Targets / Exporters              │
│  ┌──────┐ ┌──────┐ ┌────────┐ ┌───────┐ │
│  │Node  │ │MySQL │ │K8s API │ │Custom │ │
│  │Exp.  │ │Exp.  │ │Exp.   │ │App    │ │
│  └──────┘ └──────┘ └────────┘ └───────┘ │
│  ◄─ Pull (HTTP /metrics)                │
│  ─► Push (HTTP POST /api/v1/write)      │
└──────────────────────────────────────────┘
```

### 数据流详解

```
1. 指标采集流程 (Write Path):

   Target ──► Service Discovery ──► Scraper Pool ──► Pre-processor ──► In-Memory Head ──►
                                                                                    │
                    ┌───────────────────────────────────────────────────────────────┘
                    ▼
   ┌─────────────────────┐
   │  Scraper (Collector) │:
   │  ┌─────────────────┐ │
   │  │ 1. DNS/Consul   │ │  发现目标服务
   │  │ 2. HTTP GET     │ │  拉取 /metrics
   │  │ 3. Text Parser  │ │  解析 Prometheus 文本格式
   │  │ 4. Label Rewrite│ │  标签重写/过滤
   │  │ 5. Sample App.  │ │  采样 (如果有配置)
   │  │ 6. Push to Queue│ │  写入消息队列
   │  └─────────────────┘ │
   └──────────┬───────────┘
              ▼
   ┌─────────────────────┐
   │  Write Pipeline:     │
   │  ┌─────────────────┐ │
   │  │ Message Queue   │ │  Kafka (持久化缓冲)
   │  │ (Kafka/Redpanda)│ │  防止后端过载丢数据
   │  └────────┬────────┘ │
   │           ▼           │
   │  ┌─────────────────┐ │
   │  │ Time Series DB  │ │  写入 Ingestor
   │  │ Ingestor Pool   │ │  内存 append + WAL
   │  └─────────────────┘ │
   └─────────────────────┘

2. 查询流程 (Read Path):

   Query ──► Parser ──► Planner ──► Executor ──► Aggregator ──► Response
              │            │
              ▼            ▼
   PromQL → AST → 物理执行计划 → 分布式查询执行

   ┌──────────────────────────────────────────────────────────┐
   │ PromQL 查询执行流程:                                      │
   │                                                          │
   │ 输入: rate(http_requests_total{job="api"}[5m])           │
   │                                                          │
   │ 步骤:                                                    │
   │ 1. Parser: 解析 PromQL → AST                             │
   │ 2. Label Matcher: {job="api"} → 查找倒排索引 → [s1,s2,s3]│
   │ 3. Range Selector: [5m] → 读取5分钟内 chunks             │
   │ 4. Function: rate() → 计算每秒增长率                     │
   │ 5. 返回: vector [{metric: labels, value: 123.45}]        │
   └──────────────────────────────────────────────────────────┘

3. 告警流程:

   ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐
   │ Rule     │    │  Evaluator   │    │  Alert       │    │  Alert     │
   │ Storage  │───►│  (每30s评估) │───►│  State Store │───►│  Manager   │
   └──────────┘    └──────┬───────┘    └──────┬───────┘    └─────┬──────┘
                          │                    │                  │
           ◄──────────────┘                    │                  │
       查询指标判断阈值                         │                  │
                                               ▼                  ▼
                                     ┌──────────────┐   ┌────────────────┐
                                     │ pending →    │   │  群聊/分组/认领  │
                                     │ firing  →    │   │  去重/抑制       │
                                     │ resolved     │   │  通知分发       │
                                     └──────────────┘   └────────────────┘
```

## 核心深入

### 1. Pull vs Push 模式对比 (Prometheus vs Graphite/influxDB)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Pull 模型 (Prometheus)                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐         │
│  │ Monitoring   │────►│  Target App  │────►│  Target App  │         │
│  │ Server       │     │  :9090/metric│     │  :9091/metric│         │
│  │              │◄────│  (HTTP GET)  │     │  (HTTP GET)  │         │
│  └──────────────┘     └──────────────┘     └──────────────┘         │
│                                                                     │
│  优点: 服务发现简单，健康检查自然集成，无需中间缓冲                      │
│  缺点: 短生命周期任务数据可能丢失，防火墙/NAT 问题                      │
├─────────────────────────────────────────────────────────────────────┤
│                        Push 模型 (InfluxDB/Graphite)                │
│  ┌──────────────┐     ┌──────────────┐                              │
│  │  Target App  │────►│  Push Gateway│────► Monitoring Server       │
│  │  POST /write │     │  (Buffer)    │                              │
│  └──────────────┘     └──────────────┘                              │
│                                                                     │
│  优点: 短生命周期任务友好，无 NAT 问题，SDK 集成简单                    │
│  缺点: 难以区分"没有数据"和"目标宕机"，限流困难，需要外部缓冲区          │
└─────────────────────────────────────────────────────────────────────┘

最佳实践: 同时支持 Pull + Push，提供 Push Gateway 作为代理
```

### 2. 时序数据库存储引擎设计

```
┌──────────────────────────────────────────────────────────────┐
│                    TSDB 存储引擎架构                          │
│                                                              │
│   ┌───────────────────────────────────────────────────────┐  │
│   │                  WAL (Write-Ahead Log)                 │  │
│   │  顺序写入，崩溃恢复，每个 Ingestor 独立 WAL              │  │
│   └───────────────────────┬───────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│   ┌───────────────────────────────────────────────────────┐  │
│   │              Active Head Block (Memory)               │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│   │  │ Chunk A     │  │ Chunk B     │  │ Chunk C     │    │  │
│   │  │ (2h window) │  │ (2h window) │  │ (2h window) │    │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│   │  每个 Chunk 包含 120 个 sample (15s interval × 2h)     │  │
│   └───────────────────────┬───────────────────────────────┘  │
│                           │ (每 2 小时持久化)                 │
│                           ▼                                   │
│   ┌───────────────────────────────────────────────────────┐  │
│   │                Persistent Blocks (SSD)                │  │
│   │  ┌─────────────────────────────────────────────────┐  │  │
│   │  │ Index │ Chunks │ Meta.json │ tombstones          │  │  │
│   │  └─────────────────────────────────────────────────┘  │  │
│   │  每 Block 包含 N 个 series 的压缩 chunks              │  │
│   └───────────────────────┬───────────────────────────────┘  │
│                           │ (压缩合并)                        │
│                           ▼                                   │
│   ┌───────────────────────────────────────────────────────┐  │
│   │                Object Storage (S3/GCS)               │  │
│   │  长期保留 > 30天，压缩合并后的 Block 上传到对象存储     │  │
│   └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3. 压缩算法详解

```
Facebook Gorilla Paper (2015) 时序数据压缩算法:

Timestamp 压缩 (Delta-of-Delta):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
假设采集间隔是 60s, 第一个 timestamp = 1483228800

T0 = 1483228800  (base, 存完整64bit)
T1 = 1483228860 → delta D = 60
T2 = 1483228920 → delta D = 60 → DOD = 0
T3 = 1483228980 → delta D = 60 → DOD = 0
T4 = 1483228985 → delta D = 5  → DOD = -55 (异常, 用更多 bit)

编码表:
- DOD = 0            → bit '0' (1 bit, 最常见)
- DOD ∈ [-8191, 8192] → bits '10' + 14 bits value
- DOD ∈ [-65535, 65536]→ bits '110' + 17 bits value
- 其他 → bits '111' + 32 bits value

平均值: 1.37 bits/timestamp

Value 压缩 (XOR):
━━━━━━━━━━━━━━━━━━
float64 的 XOR 结果:

V0 = 3.14     (存完整 64 bits)
V1 XOR V0 = 0x000000000000000 → bit '0' (1 bit)
V2 XOR V1 = 0x001000000000000 → bits '10' + leading_zeros(5) + meaningful_bits(1)
V3 XOR V2 = 0x001200000000000 → bits '11' + leading_zeros(5) + meaningful_bits(9)

平均值: 1.37 bits/value

总计: 每个数据点约 2.74 bytes (vs 原生 16 bytes, 压缩比 ~5.8x)
```

### 4. 倒排索引 (Inverted Index) 查询优化

```
┌─────────────────────────────────────────────────────────────────┐
│                   标签倒排索引                                   │
│                                                                 │
│  Series 1: __name__=http_req, method=GET, status=200             │
│  Series 2: __name__=http_req, method=POST, status=200            │
│  Series 3: __name__=http_req, method=GET, status=500             │
│  Series 4: __name__=grpc_req, service=User, method=GetUser       │
│                                                                 │
│  倒排索引结构:                                                   │
│  ┌──────────────────────────────────────────────────┐          │
│  │  __name__="http_req" → Posting List [1, 2, 3]    │          │
│  │  method="GET"       → Posting List [1, 3]        │          │
│  │  method="POST"      → Posting List [2]           │          │
│  │  status="200"       → Posting List [1, 2]        │          │
│  │  status="500"       → Posting List [3]           │          │
│  │  __name__="grpc_req"→ Posting List [4]           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  查询: http_req{method="GET", status="200"}                      │
│  执行: Intersect(Posting[__name__=http_req],                     │
│                  Posting[method=GET],                            │
│                  Posting[status=200]) → [1]                      │
│  优化: 从最小 Posting List 开始交，使用 Roaring Bitmap            │
└─────────────────────────────────────────────────────────────────┘

Roaring Bitmap 优化:
使用 Roaring Bitmap 替代普通 Posting List:
- 稀疏区间用 sorted array
- 密集区间用 bitmap
- 交集操作极快 (SIMD 加速)
- 内存占用小
```

### 5. 告警系统设计

```
┌──────────────────────────────────────────────────────────────┐
│                    Alerting Pipeline                          │
│                                                              │
│  规则定义示例:                                                │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ alert: HighErrorRate                                      ││
│  │ expr: rate(http_requests_total{job="api"}                  ││
│  │       {status=~"5.."}[5m])                                ││
│  │       /                                                   ││
│  │       rate(http_requests_total{job="api"}[5m])            ││
│  │       > 0.05                                             ││
│  │ for: 5m                                                   ││
│  │ labels:                                                    ││
│  │   severity: critical                                      ││
│  │ annotations:                                               ││
│  │   summary: "High error rate on {{ $labels.instance }}"    ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  状态机:                                                     │
│                                                              │
│       ┌──────────┐                                           │
│       │ Inactive │── 条件满足 ──► ┌─────────┐                │
│       └──────────┘               │ Pending  │                │
│            ▲                     └────┬─────┘                │
│            │                          │                      │
│            │                     for duration 满足            │
│            │                          │                      │
│            │                          ▼                      │
│       ┌──────────┐  ←── 条件恢复 ─┐ ┌─────────┐             │
│       │ Resolved │               │ │ Firing   │────► 通知    │
│       └──────────┘               └─┴─────────┘              │
│                                                              │
│  关键设计考量:                                                │
│  1. Silencing: 已知维护窗口静默告警                           │
│  2. Inhibition: 高阶告警抑制低阶 (如整机Down抑制服务Down)      │
│  3. Grouping: 相同 alertname 聚合为一条通知                   │
│  4. Deduplication: 多实例告警去重 (按 fingerprint)            │
│  5. Escalation: 告警升级机制，超时自动升级                    │
└──────────────────────────────────────────────────────────────┘
```

### 6. PromQL 执行引擎

```
┌────────────────────────────────────────────────────────────────┐
│                     PromQL 执行优化                             │
│                                                                │
│  查询: sum(rate(http_requests_total[5m])) by (service)         │
│                                                                │
│  执行计划:                                                     │
│  ┌──────────────────────────────────────────────────────┐     │
│  │                     SUM (by service)                   │     │
│  │                         │                             │     │
│  │                    ┌────┴────┐                        │     │
│  │                  rate()   rate()                      │     │
│  │                    │        │                         │     │
│  │               Selector  Selector                      │     │
│  │               [s1,s2]   [s3,s4]                      │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  优化技术:                                                     │
│  1. 查询分片 (Query Sharding): 按 hash(series_id) 分片并行查询 │
│  2. 结果缓存 (Query Result Cache): 相同查询缓存N秒             │
│  3. 下推聚合 (Pushdown): 在存储节点完成 rate() 后再 sum        │
│  4. 向量化执行: SIMD 加速数值计算                              │
│  5. 惰性求值: 只计算所需时间段的 chunks                        │
│                                                                │
│  分片查询执行示例:                                             │
│  ┌────────┐  ┌────────┐  ┌────────┐                           │
│  │Shard 0│  │Shard 1│  │Shard 2│                           │
│  │[s1,..]│  │[s2,..]│  │[s3,..]│                           │
│  └───┬────┘  └───┬────┘  └───┬────┘                           │
│      │ rate()    │ rate()    │ rate()                          │
│      ▼           ▼           ▼                                 │
│  ┌──────────────────────────────────┐                         │
│  │         Query Merger             │                         │
│  │         Final Aggregation        │                         │
│  └──────────────────────────────────┘                         │
└────────────────────────────────────────────────────────────────┘
```

### 7. Service Discovery 服务发现

```
┌──────────────────────────────────────────────────────────────┐
│                    服务发现机制                                │
│                                                              │
│  支持的发现方式:                                              │
│                                                              │
│  1. Static Config:                                           │
│     ┌──────────────────────────────────────────────┐        │
│     │ scrape_configs:                                │        │
│     │   - job_name: 'my-api'                        │        │
│     │     static_configs:                            │        │
│     │       - targets: ['10.0.0.1:9090','10.0.0.2:9090']│     │
│     └──────────────────────────────────────────────┘        │
│                                                              │
│  2. DNS-based:                                               │
│     ┌──────────────────────────────────────────────┐        │
│     │ dns_sd_configs:                                │        │
│     │   - names: ['api.example.com']                │        │
│     │     type: 'A'                                  │        │
│     │     port: 9090                                 │        │
│     └──────────────────────────────────────────────┘        │
│                                                              │
│  3. Kubernetes:                                              │
│     ┌──────────────────────────────────────────────┐        │
│     │ kubernetes_sd_configs:                         │        │
│     │   - role: pod                                  │        │
│     │     namespaces:                                 │        │
│     │       names: ['production']                    │        │
│     └──────────────────────────────────────────────┘        │
│                                                              │
│  4. Consul/Etcd:                                             │
│     ┌──────────────────────────────────────────────┐        │
│     │ consul_sd_configs:                             │        │
│     │   - server: 'consul:8500'                     │        │
│     │     services: ['api', 'worker', 'cache']       │        │
│     └──────────────────────────────────────────────┘        │
│                                                              │
│  内部实现: Hash Ring 分片分配 Target                          │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  Scraper Pool (N 个实例)                                  ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                 ││
│  │  │Scraper 1 │ │Scraper 2 │ │Scraper 3 │                 ││
│  │  │targets:  │ │targets:  │ │targets:  │                 ││
│  │  │ [t1,t2,t5]│ │[t3,t6,t8]│ │[t4,t7,t9]│                 ││
│  │  └──────────┘ └──────────┘ └──────────┘                 ││
│  │                                                          ││
│  │  使用 Consist Hash Ring 分配:                             ││
│  │  hash(target) → find node on ring → assign               ││
│  │  节点变更时只重新分配少量 target                           ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

## 扩展性与高可用

### 水平扩展策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                    水平扩展架构                                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Load Balancer                             │   │
│  └───┬──────────────┬──────────────┬───────────────────────┬───┘   │
│      │              │              │                       │        │
│      ▼              ▼              ▼                       ▼        │
│  ┌────────┐    ┌────────┐    ┌────────┐              ┌────────┐    │
│  │Ingestor│    │Ingestor│    │Ingestor│   ...        │Ingestor│    │
│  │Group 0 │    │Group 1 │    │Group 2 │              │Group N │    │
│  │        │    │        │    │        │              │        │    │
│  │WAL ▐SSD│    │WAL ▐SSD│    │WAL ▐SSD│              │WAL ▐SSD│    │
│  └───┬────┘    └───┬────┘    └───┬────┘              └───┬────┘    │
│      │             │             │                        │         │
│      └─────────────┼─────────────┼────────────────────────┘         │
│                    │             │                                  │
│                    ▼             ▼                                  │
│              ┌──────────────────────────────────┐                   │
│              │     Object Storage (S3/GCS)       │                   │
│              │   Compactor 定期合并压缩 Blocks    │                   │
│              └──────────────────────────────────┘                   │
│                                                                     │
│  Ingestor 分组策略:                                                 │
│  - 按 hash(series_id) % num_groups 分配到不同 Ingestor Group        │
│  - 每个 Group 内使用 Raft 共识，确保多副本一致性                      │
│  - 查询时按相同 hash 路由到对应 Group                               │
│                                                                     │
│  Compactor:                                                         │
│  - 独立的批处理任务，将多个 small blocks 合并为 larger blocks         │
│  - 执行数据去重 (dedup)、乱序数据排序、墓碑清理                        │
│  - 按时间范围分区，每次 compact 固定的时间窗口                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 高可用设计

```
┌──────────────────────────────────────────┐
│        高可用策略                         │
│                                          │
│  1. 写路径高可用:                         │
│     ┌────────────────────────────┐       │
│     │ Kafka Queue (默认7天保留)   │       │
│     │ 后端故障时数据不丢失        │       │
│     │ 恢复后重放消费              │       │
│     └────────────────────────────┘       │
│                                          │
│  2. 存储层高可用:                         │
│     ┌────────────────────────────┐       │
│     │ Raft 共识复制 (3副本)       │       │
│     │ WAL 持久化 (mmap + fsync)  │       │
│     │ Ingestor 故障 → 自动切主    │       │
│     └────────────────────────────┘       │
│                                          │
│  3. 查询层高可用:                         │
│     ┌────────────────────────────┐       │
│     │ Querier 无状态 (stateless)  │       │
│     │ 多副本部署                  │       │
│     │ 查询路由 → 健康 Ingestor   │       │
│     └────────────────────────────┘       │
│                                          │
│  4. 告警引擎高可用:                       │
│     ┌────────────────────────────┐       │
│     │ Ruler 多副本 + Leader选举   │       │
│     │ 使用 Etcd 做 Leader Lease  │       │
│     │ 告警状态持久化到 DB         │       │
│     └────────────────────────────┘       │
└──────────────────────────────────────────┘
```

### 监控与运维 (Meta-Monitoring)

```
重要: 监控系统本身也需要被监控!

监控项目:
1. 写延迟 (p50/p95/p99)
2. 查询延迟 (p50/p95/p99)
3. Ingestor 内存使用率、GC 频率
4. Kafka Consumer Lag
5. Compactor 积压
6. 告警评估延迟
7. 磁盘 IO 使用率
8. 网络带宽利用率

告警规则:
- Ingestor CPU > 80% for 10m
- Kafka Consumer Lag > 10000 for 5m
- Query Latency p99 > 5s for 5m
- WAL Disk Usage > 85%
```

## 总结

| 维度 | 技术选型 | 理由 |
|------|---------|------|
| 采集模式 | Pull + Push Gateway | 兼顾长生命周期和短生命周期任务 |
| 存储引擎 | 自研 TSDB (Gorilla压缩) | 极致压缩率，时序数据专用优化 |
| 消息队列 | Kafka | 高吞吐持久化缓冲 |
| 索引 | 倒排索引 + Roaring Bitmap | O(1) 标签查找 |
| 查询语言 | PromQL兼容 | 业界标准 |
| 复制协议 | Raft | 强一致性 |
| 对象存储 | S3/GCS | 成本低，长期保留 |
| 服务发现 | Consul/K8s API | 云原生生态集成 |
| 告警去重 | 基于 fingerprint 哈希 | 多实例告警合并 |

核心设计要点:
1. **存储即索引**: 倒排索引 + 列存 chunk 的结合，查询不需要全表扫描
2. **压缩是关键**: Gorilla 压缩将数据量降低5-8倍，大幅降低存储成本
3. **Pull 为主，Push 为辅**: 服务发现自然集成，故障检测内置
4. **告警状态机**: Pending → Firing → Resolved，引入 for duration 避免抖动
5. **分片与路由**: 按 series_id hash 分片，查询路由并行化
6. **WAL 先行**: 所有写入先落 WAL，保证数据不丢失
