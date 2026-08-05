# 39. 设计分布式链路追踪系统 (Distributed Tracing like Jaeger/Zipkin)

## 题目
设计一个分布式链路追踪系统，用于监控和诊断微服务架构中的请求链路。类似 Jaeger、Zipkin、AWS X-Ray、Google Dapper。

---

## 需求澄清

### 功能性需求
- 自动追踪跨服务的请求链路（Span），记录操作名、起止时间、Tags、Logs
- Trace ID 跨进程传播（HTTP/gRPC/Kafka Header）
- 自适应采样策略（Head+Tail混合）
- 可视化展示调用链（瀑布图/甘特图）+ 服务依赖拓扑图
- 延迟分析（P50/P95/P99），错误追踪与根因分析
- 支持按 TraceID、ServiceName、时间范围搜索

### 非功能性需求

| 指标 | 要求 |
|------|------|
| 数据量 | 每秒百万级 Span |
| 存储 | TB 级，支持多级存储 |
| 采样 | 自适应采样，开销 <1% |
| 可查询延迟 | 写入到可搜索 < 10s |
| 可用性 | 99.9%，追踪故障不影响业务 |

### 容量估算
- 全局 QPS 100K，平均调用链深度 10 → 1,000,000 spans/s
- 每 Span ~1KB → 1GB/s 原始数据
- 采样率 10%（头部采样），实际存储 100MB/s
- 每天 8.6TB，7天热数据 60TB

---

## 核心数据模型

```json
{
  "traceId": "abc123def456",
  "spanId": "span001",
  "parentSpanId": null,
  "operationName": "GET /api/orders/123",
  "serviceName": "gateway",
  "startTime": 1700000000000000,
  "duration": 200000,
  "status": "OK",
  "tags": {
    "http.method": "GET",
    "http.status_code": 200,
    "component": "spring-webmvc"
  },
  "logs": [{"timestamp": 1700..., "fields": {"event": "cache_miss"}}],
  "references": [{"refType": "CHILD_OF", "traceId": "abc...", "spanId": "parentSpan001"}]
}
```

---

## 高层次架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Instrumented Apps: [Service A] [Service B] [Service C]                    │
│ (OpenTelemetry SDK: Sampler → Processor → Exporter)                       │
│ Context Propagation: traceparent Header (W3C TraceContext)                │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Collector Cluster (Stateless): 校验 → 缓冲 → 批量写入 Kafka               │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Kafka: spans-topic (RF=3, Retention 48h, 缓冲+削峰)                       │
└─────────┬──────────────────┬──────────────────────┬──────────────────────┘
          ▼                  ▼                      ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│ Span Writer  │   │ Stream Proc  │   │ Tail Sampler         │
│ → Cassandra  │   │ (Flink)      │   │ 错误/慢请求 100%保留  │
│ → ES(索引)   │   │ 服务依赖图   │   └──────────────────────┘
└──────────────┘   └──────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Storage: Cassandra(按TraceID查询) + Elasticsearch(按服务/操作搜索)        │
│         S3(归档 > 7天)                                                    │
└──────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Query & UI: Jaeger UI / Grafana / Alerting                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. Context Propagation

Go 语言示例：

```go
// W3C TraceContext: traceparent: 00-{trace-id}-{parent-id}-{trace-flags}
// 例: 00-0af765...b211c8-b7ad6b...03331-01

type Span struct {
    TraceID, SpanID, ParentID string
    Operation string
    StartTime time.Time
    Duration  time.Duration
    Tags      map[string]string
}

func (t *Tracer) StartSpan(name string, parent *Span) *Span {
    s := &Span{Operation: name, StartTime: time.Now(), Tags: make(map[string]string)}
    if parent != nil {
        s.TraceID = parent.TraceID
        s.ParentID = parent.SpanID
        s.SpanID = generateID()
    } else {
        s.TraceID = generateID()
        s.SpanID = s.TraceID // root span
    }
    return s
}

func (s *Span) Finish() {
    s.Duration = time.Since(s.StartTime)
    reporter.EnqueueAsync(s) // 异步入队, 不阻塞
}

// HTTP注入与提取
func Inject(span *Span, req *http.Request) {
    req.Header.Set("traceparent", fmt.Sprintf("00-%s-%s-01", span.TraceID, span.SpanID))
}

func Extract(req *http.Request) *Span {
    parts := strings.Split(req.Header.Get("traceparent"), "-")
    if len(parts) != 4 { return nil }
    return &Span{TraceID: parts[1], ParentID: parts[2]}
}
```

### 2. 采样策略：Head + Tail

```
┌───────────────────────────────────────────────────────┐
│ Head Sampling: Trace开始时决定是否采样                   │
│   固定概率: 0.1%~10% / 自适应: rate=target/actualQPS   │
│   优点: 减少全链路开销                                   │
│   缺点: 可能丢失错误Trace                               │
├───────────────────────────────────────────────────────┤
│ Tail Sampling: 请求完成后决定是否保留                    │
│   错误(status=ERROR) → 100%                            │
│   延迟 > 2×P95 → 100%                                  │
│   正常请求: 按概率保留                                   │
│   优点: 不漏重要Trace                                   │
│   缺点: 需要Snapshots缓冲                               │
├───────────────────────────────────────────────────────┤
│ 混合 (推荐): Head自适应(基础样本) + Tail补漏(错误/慢)     │
└───────────────────────────────────────────────────────┘
```

### 3. 自适应采样器

```python
class AdaptiveSampler:
    def __init__(self, target_sps=100):
        self.target = target_sps
        self.rate = 1.0
        self.counter = 0

    def should_sample(self):
        self.counter += 1
        if self.counter % 1000 == 0:
            self.rate = min(1.0, self.target / (self.counter / 10.0))
            self.counter = 0
        return random.random() < self.rate
```

### 4. 数据存储：Cassandra + Elasticsearch

```sql
-- Cassandra (按 traceId 查全量, Write-optimized)
CREATE TABLE traces (
    trace_id    blob,
    span_id     bigint,
    parent_id   bigint,
    operation_name text,
    service_name   text,
    start_time  bigint,
    duration    bigint,
    tags        list<frozen<tuple<text,text>>>,
    PRIMARY KEY (trace_id, span_id)
);

-- Elasticsearch (按服务/操作/时间搜索, Read-optimized)
PUT /jaeger-span-{YYYY-MM-DD}
{
  "mappings": {
    "properties": {
      "traceId": {"type": "keyword"},
      "serviceName": {"type": "keyword"},
      "operationName": {"type": "keyword"},
      "startTime": {"type": "date"},
      "duration": {"type": "long"},
      "status": {"type": "keyword"}
    }
  }
}
```

### 5. 服务依赖图（Flink 流处理）

```
从Kafka消费Span → 解析parent-child关系 → 时间窗口聚合 → ClickHouse

聚合产出:
┌──────────┬───────────┬────────┬─────────────┬──────────────┐
│ Source   │ Target    │ Calls  │ AvgLatency  │ ErrorRate    │
├──────────┼───────────┼────────┼─────────────┼──────────────┤
│ gateway  │ user-svc  │ 12,340 │ 45ms        │ 0.1%         │
│ gateway  │ order-svc │  8,521 │ 120ms       │ 2.3%         │
│ order-svc│ inventory │  7,890 │ 50ms        │ 0.0%         │
└──────────┴───────────┴────────┴─────────────┴──────────────┘
```

### 6. 性能与容错

```
SDK性能优化:
  1. 异步上报: Span.Finish() → 内存队列 → 后台批量发送 (主线程不阻塞)
  2. 队列满时: Drop旧Span(记录Metrics) 而非 Block
  3. Span对象池: sync.Pool复用减少GC
  4. 未采样Span: 仅传traceId, 不创建完整Span

故障处理:
  Collector宕机 → SDK内存队列堆积 → 超过阈值Drop旧Span
  Kafka故障 → Producer自动重试 → 应用业务不受影响
  ES故障 → 搜索不可用但不影响写入(Cassandra正常)
```

---

### 7. 监控与告警

```
追踪系统自监控:

┌──────────────────────────┬──────────────────────────────┐
│ 指标                      │ 告警阈值                      │
├──────────────────────────┼──────────────────────────────┤
│ Span丢弃率               │ > 1% (Exporter队列满)          │
│ Collector写入延迟         │ P99 > 5s                     │
│ Kafka Consumer Lag       │ > 50000                      │
│ ES/ClkHouse写入拒绝       │ > 0.5%                       │
│ 数据查询延迟              │ P95 > 3s                     │
│ 各服务Instrumentation覆盖率│ < 95% 新增服务未接入          │
└──────────────────────────┴──────────────────────────────┘
```

### 8. 数据保留策略 (TTL)

```
多级存储与TTL:

┌──────────────────────────────────────────────────────────────┐
│ Hot 存储 (Cassandra/ES, 7天):                                │
│   完整Span数据，支持全功能查询                                 │
│                                                              │
│ Warm 存储 (ES/ClickHouse, 30天):                              │
│   降采样后的聚合数据，支持趋势分析                              │
│   仅保留关键字段: traceId, serviceName, duration, status      │
│                                                              │
│ Cold 存储 (S3 Parquet, 90天):                                 │
│   列式压缩归档，仅按需查询(需要unload到临时ES)                  │
│                                                              │
│ Archive (S3 Glacier, 1年+):                                   │
│   合规审计保留，查询需要提前请求unarchive                       │
└──────────────────────────────────────────────────────────────┘

TTL 配置:
  - Cassandra: USING TTL 604800 (7天)
  - ES ILM: hot(7d) → warm(30d) → delete(30d)
  - S3 Lifecycle: 90天后转Glacier
```

### 9. Trace 查询流程

```
用户查询某Trace的完整链路:

  1. 用户在 Jaeger UI 输入 traceId
  2. Query Service 收到请求:
     a. 先在 Elasticsearch 中搜索 traceId → 找到Target Storage Tier
     b. 如果trace在Hot层 → 从Cassandra查询所有Spans
     c. 如果trace在Warm层 → 从ES查询聚合数据
     d. 如果trace在Cold层 → 从S3加载原始数据(慢查询)
  3. 组装所有Span → 构建树形依赖关系 (parent_span_id)
  4. 计算每个Span的深度、关键路径、高亮瓶颈Span
  5. 返回瀑布图 (Waterfall/Gantt Chart) 展示
```

### 10. 与日志/指标系统的关联

```
可观测性三位一体:

┌─────────────────────────────────────────────────────────────┐
│ Metrics (指标)    → 发现问题 "支付服务P99延迟上升了"          │
│ Tracing (追踪)    → 定位问题 "是这个trace的哪一步慢了"        │
│ Logging (日志)    → 分析根因 "这一步报了什么错"              │
│                                                             │
│ 关联方式:                                                    │
│   traceId注入到日志中 (MDC/slog)                              │
│   Metrics带exemplar: 保存一个代表性traceId                     │
│                                                             │
│ 日志示例:                                                    │
│   [traceId=abc123] [spanId=span001] ERROR: payment timeout  │
│                                                             │
│ Grafana 集成:                                                │
│   Dashboard显示Prometheus指标 → 点击异常点                    │
│   → 跳转到Jaeger → 查看该时刻的采样Trace                      │
│   → 从Trace日志跳转到Kibana → 查看完整的上下文日志             │
└─────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 数据模型 | Trace → Span 树形结构, W3C TraceContext 标准 |
| 采样策略 | Head自适应(基础) + Tail补漏(错误100%, 慢100%) |
| Context Propagation | HTTP/gRPC/Kafka Header, <80B/request |
| 存储 | Cassandra(按TraceID) + ES(按服务/操作搜索) + S3(归档) |
| 存储分层 | Hot(7d,Cassandra) → Warm(30d,ES聚合) → Cold(90d,S3) |
| 处理层 | Kafka缓冲 + Collector批量写入 + Flink依赖图聚合 |
| 性能 | 异步上报 + 批量 + 对象池, 开销<1% |
| 可观测性关联 | traceId注入日志 + Metrics exemplar → 三位一体 |

**CAP 取舍:** 链路追踪是 AP 系统。追踪数据宁可丢弃也不应阻塞业务请求。Collector 故障时 SDK 直接丢弃 Span，追踪查询短暂不可用不影响业务。ES搜索可能返回稍旧数据(最终一致性)。

**关键权衡:**
1. **Head vs Tail 采样:** Head省资源但漏数据(特别是错误)，Tail不漏但需要更大缓冲。混合方案最优
2. **Cassandra vs ES:** Cassandra写效率高成本低(适合全量Spans)；ES搜索灵活但写成本高(适合索引)。双写各取所长
3. **异步 vs 同步上报:** 异步保证业务零开销，代价是极端队列满时可能丢Span。这是可接受的权衡
4. **存储成本 vs 数据价值:** 全量Trace存储成本极高。通过分层TTL(7d→30d→90d→Archive)在成本和可用性间找到平衡
5. **SDK侵入性 vs 功能完整性:** Auto-instrumentation(字节码注入)零代码侵入但Span细节有限；Manual instrumentation更精确但有代码成本
