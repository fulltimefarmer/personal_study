# 32. 设计日志系统 / ELK (Logging System)

## 题目

设计一个大规模分布式日志收集、存储、检索和分析系统，类似 ELK Stack (Elasticsearch + Logstash + Kibana) 或 Splunk。需要支持每天数十TB级别的日志数据。

---

## 需求澄清

### 功能性需求 (Functional Requirements)

- 从多种数据源收集日志（应用日志、系统日志、容器日志、网络日志）
- 日志解析与结构化（解析 JSON、正则提取字段）
- 按时间范围搜索日志
- 全文搜索，支持 AND/OR/NOT 布尔查询
- 按字段过滤（如 host=web-01, level=ERROR, service=payment）
- 日志聚合分析（按时间段统计、Top N 分析、异常检测）
- 支持实时日志流（类似 `tail -f`，数据从产生到可搜索 < 10秒）
- 日志保留策略（热数据 7天，温数据 30天，冷数据 90天+）
- 可视化仪表板（错误率趋势图、请求量曲线、告警）

### 非功能性需求 (Non-functional Requirements)

| 指标 | 要求 |
|------|------|
| 写入吞吐 | 支持 1TB+/天，峰值 100K+ events/s |
| 搜索延迟 | 简单查询 < 1s，复杂聚合 < 10s |
| 数据新鲜度 | 写入到可搜索 < 10s（准实时） |
| 可用性 | 99.9%，写入路径优先保证 |
| 数据持久性 | 日志不丢失，副本数 >= 2 |
| 扩展性 | 水平扩展，写入和存储独立扩展 |

### 容量估算 (Capacity Estimation)

假设中型互联网公司：
- 微服务数量：500 个
- 每服务平均日志量：2GB/天
- 总日志量：500 × 2GB = 1TB/天
- 日志事件大小：平均 512B
- 每天事件数：1TB / 512B ≈ 20亿事件
- 写入 QPS：20亿 / 86400 ≈ 23,148 events/s
- 峰值写入 QPS：23,148 × 3 ≈ 70,000 events/s

**存储估算：**
- 原始日志：1TB/天
- 索引开销：约为原始数据的 100%（倒排索引 + 列存）
- 总存储/天：约 2TB
- 副本因子 2：4TB/天
- 30天保留：120TB
- 压缩比约 4:1（日志高度可压缩）：30TB

**搜索 QPS 估算：**
- 开发+运维人员：500人
- 每人每天搜索：20次
- 总搜索量：10,000次/天 ≈ 0.1 QPS
- 仪表板自动刷新查询：每秒 50次
- 峰值搜索 QPS：约 100 QPS

---

## API 设计

### 日志写入 API

```
# 批量写入日志（主要接口）
POST /api/v1/logs/_bulk
Content-Type: application/json

{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00.123Z",
      "service": "payment-service",
      "host": "web-01.prod",
      "level": "ERROR",
      "message": "Payment timeout for order 12345",
      "trace_id": "abc123",
      "duration_ms": 5001,
      "user_id": "user789"
    },
    {
      "timestamp": "2024-01-15T10:30:00.234Z",
      "service": "payment-service",
      "host": "web-01.prod",
      "level": "INFO",
      "message": "Order 12346 processed",
      "trace_id": "abc124",
      "duration_ms": 45
    }
  ]
}

# 单条日志写入
POST /api/v1/logs
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "service": "auth-service",
  "level": "WARN",
  "message": "Rate limit approaching for IP 10.0.0.1"
}

# Syslog/Filebeat 集成 (TCP/UDP)
# 日志采集器通过专用端口发送: tcp://log-collector:5514
```

### 日志搜索 API

```
# 搜索日志
POST /api/v1/logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "service": "payment-service" }},
        { "match": { "level": "ERROR" }}
      ],
      "filter": [
        { "range": { "timestamp": { "gte": "2024-01-15T00:00:00Z",
                                    "lte": "2024-01-15T23:59:59Z" }}}
      ],
      "must_not": [
        { "match": { "message": "healthcheck" }}
      ]
    }
  },
  "sort": [{ "timestamp": "desc" }],
  "from": 0,
  "size": 50,
  "highlight": {
    "fields": { "message": {} }
  }
}

# 聚合查询（类似 Kibana 的图表数据源）
POST /api/v1/logs/_aggregate
{
  "query": {
    "range": { "timestamp": { "gte": "now-1h" }}
  },
  "aggs": {
    "errors_by_service": {
      "terms": { "field": "service", "size": 20 }
    },
    "errors_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "interval": "1m"
      },
      "aggs": {
        "error_count": {
          "filter": { "term": { "level": "ERROR" }}
        }
      }
    }
  }
}

# 实时日志流 (SSE - Server-Sent Events)
GET /api/v1/logs/_stream?query=level:ERROR&service=payment
# 返回实时 SSE 流
```

### 管理 API

```
# 索引管理
PUT  /api/v1/indices/:name        # 创建索引（定义字段映射）
DELETE /api/v1/indices/:name      # 删除索引
GET  /api/v1/indices              # 列出所有索引
POST /api/v1/indices/:name/_rollover  # 索引轮转

# 保留策略
PUT  /api/v1/policies/:name
{
  "name": "30-day-retention",
  "phases": {
    "hot":  { "days": 3,  "replicas": 2 },
    "warm": { "days": 30, "replicas": 1 },
    "cold": { "days": 90, "replicas": 0, "storage": "s3" },
    "delete": { "days": 365 }
  }
}

# 告警规则
POST /api/v1/alerts/rules
{
  "name": "high_error_rate",
  "condition": "count(level=ERROR) > 100 in 5m",
  "actions": ["email:oncall@company.com", "pagerduty:team-alpha"]
}
```

---

## 数据模型

### 日志文档结构

```json
{
  // 保留字段（所有日志必有）
  "@timestamp": "2024-01-15T10:30:00.123Z",
  "@source": "payment-service",
  "@host": "k8s-pod-payment-abc123",
  
  // 标准 ECS 字段 (Elastic Common Schema)
  "service": "payment-service",
  "level": "ERROR",
  "message": "Payment gateway timeout after 5000ms",
  "error": {
    "type": "TimeoutException",
    "stack_trace": "at com.payment.gateway...",
    "message": "Connection timeout"
  },
  
  // 分布式追踪
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "span_id": "b7ad6b7169203331",
  
  // 业务字段
  "order_id": "12345",
  "user_id": "user789",
  "amount": 99.99,
  "duration_ms": 5001,
  "gateway": "stripe",
  "retry_count": 3,
  
  // Kubernetes 元数据
  "kubernetes": {
    "namespace": "production",
    "pod_name": "payment-deployment-7d8f9b6c4-abc12",
    "node_name": "gke-node-pool-1-abc",
    "container_name": "payment",
    "container_image": "payment:v2.3.1"
  }
}
```

### 索引设计（时间分片策略）

```
索引命名: logs-{service}-{YYYY.MM.DD}

logs-payment-2024.01.15
logs-payment-2024.01.16
logs-auth-2024.01.15
logs-gateway-2024.01.15
...

索引分片策略:
- 主分片数: 3～5 (根据日志量)
- 副本分片数: 1 (热数据) / 0 (冷数据)
- 每分片大小: 10～50GB (推荐范围内)
- 刷新间隔: 5s (近实时搜索)
```

### 存储分层

```
┌────────────────────────────────────────────────────────────┐
│                    存储分层架构                              │
├────────────┬───────────┬───────────┬────────────────────────┤
│    层级     │  时间段    │   存储    │  性能特点              │
├────────────┼───────────┼───────────┼────────────────────────┤
│ Hot  (热)  │ 0～3天    │ SSD/NVMe  │ 读写快, 多副本          │
│ Warm (温)  │ 3～30天   │ HDD       │ 读尚可, 单副本          │
│ Cold (冷)  │ 30～90天  │ S3/Blob   │ 搜索前需加载, 可搜索压缩 │
│ Frozen(冻) │ 90天+     │ S3/Glacier│ 不可直接搜索, 需解冻    │
└────────────┴───────────┴───────────┴────────────────────────┘
```

---

## 高层次架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            数据采集层 (Data Collection)                    │
│                                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐                │
│  │Filebeat │  │Metricbeat│  │Fluentd   │  │Prometheus │                │
│  │(文件日志)│  │(指标)    │  │(容器日志) │  │(Exporter) │                │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘                │
│       │            │             │               │                       │
└───────┼────────────┼─────────────┼───────────────┼───────────────────────┘
        │            │             │               │
        ▼            ▼             ▼               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          消息队列层 (Buffer Layer)                        │
│                                                                          │
│                     ┌──────────────────────────┐                         │
│                     │    Kafka Cluster          │                         │
│                     │  ┌──────┐ ┌──────┐ ┌────┐│                         │
│                     │  │Topic │ │Topic │ │    ││                         │
│                     │  │ logs │ │metrics│     ││                         │
│                     │  │p100+ │ │  p20 │ │...││                         │
│                     │  └──────┘ └──────┘ └────┘│                         │
│                     └──────────────────────────┘                         │
│                          削峰填谷, 持久化缓冲                               │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        处理/索引层 (Processing Layer)                      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Logstash Pool   │  │  Flink/Spark     │  │  Indexing        │      │
│  │  (解析/过滤)      │  │  Streaming       │  │  Workers         │      │
│  │                  │  │  (聚合/告警)      │  │  (写入ES)         │      │
│  │  - Parse JSON    │  │                  │  │                  │      │
│  │  - Grok/Regex    │  │  - 窗口聚合      │  │  - Bulk Index    │      │
│  │  - Field Extract │  │  - 异常检测      │  │  - Retry Logic   │      │
│  │  - Enrichment    │  │  - ML 模型       │  │  - Backpressure  │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                      │                 │
└───────────┼─────────────────────┼──────────────────────┼─────────────────┘
            │                     │                      │
            ▼                     ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         存储与搜索层 (Storage & Search)                    │
│                                                                          │
│  ┌──────────────────────────┐   ┌──────────────────────────┐           │
│  │  Elasticsearch Cluster   │   │  ClickHouse / Druid      │           │
│  │  (全文搜索 + 日志查询)    │   │  (大规模聚合分析)         │           │
│  │                          │   │                          │           │
│  │  ┌────────────────────┐  │   │  存储最近30天的指标聚合    │           │
│  │  │ Hot  Nodes (SSD)  │  │   │  比ES快 10x+ 的聚合查询    │           │
│  │  │  最近 3～7 天日志   │  │   └──────────────────────────┘           │
│  │  └────────────────────┘  │                                          │
│  │  ┌────────────────────┐  │                                          │
│  │  │ Warm Nodes (HDD)  │  │                                          │
│  │  │  3～30 天日志       │  │                                          │
│  │  └────────────────────┘  │                                          │
│  └──────────────────────────┘                                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │               S3 / Object Storage (冷数据)                │          │
│  │            存储压缩快照, 需要时可恢复到ES                   │          │
│  └──────────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           查询与可视化层                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   Kibana     │  │   Grafana    │  │   API Layer  │                   │
│  │  (日志搜索)   │  │  (指标仪表板) │  │  (程序化查询) │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │                    Alert Manager                          │          │
│  │  规则引擎 → 触发 → Email/Slack/PagerDuty/Webhook          │          │
│  └──────────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 数据写入流程

```
                   写入路径详细流程

App Node                                    Kafka                    Indexing
  │                                           │                        │
  │ 1. 写入本地日志文件                          │                        │
  │──> /var/log/app.log                       │                        │
  │                                           │                        │
  │ 2. Filebeat 监控文件尾部                    │                        │
  │──> 读取新行                                │                        │
  │                                           │                        │
  │ 3. 发送到 Kafka                            │                        │
  │──────────> kafka://logs-topic ────────────>│                        │
  │             (persisted)                     │                        │
  │             (partitioned by host)            │                        │
  │                                              │                        │
  │                                              │ 4. Consumer 消费       │
  │                                              │────> 批量拉取消息        │
  │                                              │                        │
  │                                              │ 5. 解析与处理           │
  │                                              │────> 解析JSON/Regex     │
  │                                              │────> 提取字段           │
  │                                              │────> 补充元数据         │
  │                                              │                        │
  │                                              │ 6. 批量写入ES           │
  │                                              │────> _bulk API         │
  │                                              │────> 写入主分片          │
  │                                              │────> 同步到副本分片      │
  │                                              │                        │
  │                                              │ 7. 刷新(Refresh)        │
  │                                              │────> 默认可搜索          │
```

---

## 核心深入

### 1. 倒排索引原理 (Inverted Index)

Elasticsearch 的核心数据结构，实现全文搜索的基础：

```
原始文档:
doc1: "Payment service timeout"
doc2: "User payment failed"
doc3: "Service healthcheck OK"

倒排索引构建:
┌──────────────┬─────────────────────────────┐
│     Term     │   Posting List              │
├──────────────┼─────────────────────────────┤
│   payment    │ → [doc1: pos2], [doc2: pos1] │
│   service    │ → [doc1: pos1], [doc3: pos0] │
│   timeout    │ → [doc1: pos3]              │
│   user       │ → [doc2: pos0]              │
│   failed     │ → [doc2: pos3]              │
│   healthcheck│ → [doc3: pos1]              │
│   ok         │ → [doc3: pos2]              │
└──────────────┴─────────────────────────────┘

搜索 "payment AND service":
1. 找到 "payment" 的 posting list: [doc1, doc2]
2. 找到 "service" 的 posting list: [doc1, doc3]
3. 交集 (intersection): [doc1]
4. 返回 doc1
```

**跳表 (Skip List) 优化 Posting List 合并：**

```
Posting List 1: [2, 5, 9, 15, 20, 25, 30, 35, 40]
跳表指针(n=3):   ────► ────► ────► ────► ...
                2 ───────► 15 ───────► 30

Posting List 2: [1, 3, 7, 15, 18, 22, 30, 33, 38]
跳表指针(n=3):   1 ───────► 15 ───────► 30

合并时无需逐个比较, 通过跳表直接跳到可能相交的位置:
- 比较 2 和 1 → 不相等, 跳转到15和15 → 相等! 找到交集元素
- 复杂度从 O(N+M) 降低到 O(sqrt(N)+sqrt(M))
```

### 2. 索引生命周期管理 (ILM)

```yaml
# 索引生命周期策略
policy:
  name: logs-retention-policy
  
  phases:
    hot:
      actions:
        rollover:
          max_size: 50GB        # 单个索引达50GB时轮转
          max_age: 1d            # 或者超过1天轮转
        set_priority: 100        # 恢复时优先级最高
      min_age: 0ms
    
    warm:
      min_age: 3d               # 3天后进入warm阶段
      actions:
        allocate:
          require:
            data: warm_nodes    # 迁移到warm节点
        shrink:
          number_of_shards: 1   # 缩减分片数
        forcemerge:
          max_num_segments: 1   # 合并段, 减少文件数
        set_priority: 50
    
    cold:
      min_age: 7d
      actions:
        allocate:
          require:
            data: cold_nodes
        set_priority: 0
    
    delete:
      min_age: 30d              # 30天后删除
      actions:
        delete: {}
```

### 3. 写入优化策略

```python
class IndexingOptimizer:
    """
    ES写入优化关键策略
    """
    
    # 1. Bulk API 批量写入
    def bulk_index(self, events, batch_size=5000):
        """
        批量大小选择:
        - 太小: 网络往返开销大
        - 太大: 内存压力, 单个请求超时
        - 推荐: 5～15MB per batch
        """
        for i in range(0, len(events), batch_size):
            batch = events[i:i+batch_size]
            self.es.bulk(body=batch, 
                        refresh='false',  # 不立即刷新
                        request_timeout=60)
    
    # 2. 刷新间隔调优
    def configure_index(self, index_name):
        self.es.indices.put_settings(index=index_name, body={
            "refresh_interval": "30s",  # 默认1s改为30s
            # 降低刷新频率可以减少segment数量, 提高写入吞吐
        })
    
    # 3. Translog 设置
        self.es.indices.put_settings(index=index_name, body={
            "translog": {
                "durability": "async",  # 异步刷盘
                "sync_interval": "30s"  # 每30s fsync一次
                # 注意: 可能丢失30s内的数据(可接受, 因为有Kafka)
            }
        })
    
    # 4. 预定义Mapping避免动态映射开销
    def create_index_with_mapping(self, index_name):
        self.es.indices.create(index=index_name, body={
            "mappings": {
                "dynamic": "false",  # 禁止动态映射(减少开销)
                "properties": {
                    "@timestamp": {"type": "date"},
                    "service": {"type": "keyword"},        # 不分词, 精确匹配
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},           # 分词, 全文搜索
                    "trace_id": {"type": "keyword"},
                    "duration_ms": {"type": "integer"},
                    "host": {"type": "keyword"}
                }
            }
        })
```

### 4. 搜索优化策略

```
搜索路径优化:

查询请求
    │
    ▼
┌─────────────────┐
│ Query Parser    │ ← 解析用户查询语法
└────────┬────────┘
         │
    ┌────▼────┐
    │  Rewrite│ ← Query Rewriting: 优化查询结构
    └────┬────┘      例如: date range + keyword → 重写为 filter context
         │
    ┌────▼────────────────────┐
    │  Routing to Shards      │ ← 按索引名+日期路由到相关分片
    │  (避免全分片扫描)         │
    └────┬────────────────────┘
         │
    ┌────▼────┐
    │  Cache  │ ← 检查以下缓存:
    └────┬────┘   1. Query Cache (查询结果缓存, LRU)
         │        2. Field Data Cache (聚合缓存)
         │        3. Request Cache (整个请求缓存)
         │        4. Page Cache (OS级别的磁盘缓存)
    ┌────▼────┐
    │  Execute│
    └────┬────┘
         │
    ┌────▼────┐
    │  Reduce │ ← 合并各分片结果, 排序, 截取
    └─────────┘
```

**Filter Context vs Query Context:**

```json
{
  "query": {
    "bool": {
      // Filter Context: 不计算相关性分数, 可缓存, 快
      "filter": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ],
      // Query Context: 计算相关性分数, 不可缓存, 慢
      "must": [
        { "match": { "message": "payment timeout" } }
      ]
    }
  }
}
```

### 5. Kafka 作为缓冲层的重要性

```
为什么不直接写入ES?

场景1: 无Kafka缓冲
  App → 直接写入 ES → ES过载 → 写入拒绝 → 日志丢失
  解决: 应用端重试 → 应用性能受影响, 内存积压 → OOM

场景2: 有Kafka缓冲
  App → Kafka → ES
  - Kafka 提供持久化: 消息写入即持久化, 不丢失
  - Kafka 提供削峰: 峰值写入入Kafka, ES慢慢消费
  - Kafka 提供多消费: 同一份日志可以被多个Consumer消费
    - Consumer 1: 写入ES(搜索)
    - Consumer 2: 写入S3归档
    - Consumer 3: 实时计算(Flink)聚合告警
```

### 6. 日志解析 (Log Parsing)

```python
# Grok Pattern 示例
# 原始日志: 192.168.1.1 - - [15/Jan/2024:10:30:00 +0000] "GET /api/users HTTP/1.1" 200 1234

NGINX_ACCESS_PATTERN = (
    r'%{IP:client_ip} '
    r'- - '
    r'\[%{HTTPDATE:@timestamp}\] '
    r'"%{WORD:method} %{URIPATHPARAM:request} HTTP/%{NUMBER:http_version}" '
    r'%{NUMBER:status_code} '
    r'%{NUMBER:body_bytes_sent}'
)

# 结构化后:
# {
#   "client_ip": "192.168.1.1",
#   "@timestamp": "2024-01-15T10:30:00.000Z",
#   "method": "GET",
#   "request": "/api/users",
#   "http_version": "1.1",
#   "status_code": 200,
#   "body_bytes_sent": 1234
# }

# 多层日志解析策略
class LogParser:
    def parse(self, raw_log):
        # Layer 1: 结构化日志 (JSON) — 最快
        try:
            return json.loads(raw_log)
        except JSONDecodeError:
            pass
        
        # Layer 2: 半结构化 (key=value)
        kv = self.try_key_value(raw_log)
        if kv: return kv
        
        # Layer 3: Grok 模式匹配 (正则) — 最慢但最灵活
        for pattern in self.grok_patterns:
            match = re.match(pattern, raw_log)
            if match:
                return match.groupdict()
        
        # Layer 4: Fallback — 整行作为message字段
        return {"message": raw_log}
```

---

## 扩展性与高可用

### 1. Elasticsearch 集群扩展

```
集群节点角色分离:

┌────────────────────────────────────────────────┐
│                  Master Nodes (3)              │
│  管理集群状态, 索引创建/删除, 分片分配           │
│  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      │
│  quorum = (3/2)+1 = 2, 容忍1个节点故障          │
└────────────────────┬───────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│ Data    │    │Data      │    │Data      │
│ Node 1  │    │Node 2    │    │Node 3    │
│ (Hot)   │    │(Hot)     │    │(Hot)     │
│ P0,R1   │    │P1,R2     │    │P2,R0     │
└─────────┘    └──────────┘    └──────────┘
                                           │
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │Data     │    │Data      │    │Data      │
    │ Node 4  │    │ Node 5   │    │ Node 6   │
    │ (Warm)  │    │ (Warm)   │    │ (Warm)   │
    └─────────┘    └──────────┘    └──────────┘

    ┌─────────┐    ┌──────────┐
    │Coord    │    │Coord     │    ← Coordinating Nodes (无数据, 仅路由)
    │ Node 1  │    │Node 2    │
    └─────────┘    └──────────┘
```

### 2. 多数据中心部署

```
                     Region A (Primary)           Region B (DR)
                    ┌──────────────────┐       ┌──────────────────┐
 App Logs ────────► │ Kafka Cluster A  │       │ Kafka Cluster B  │
                    │        │         │       │        │         │
                    │   ┌────▼─────┐   │       │   ┌────▼─────┐   │
                    │   │ ES Hot   │   │       │   │ ES Hot   │   │
                    │   │ ES Warm  │   │       │   │ ES Warm  │   │
                    │   └──────────┘   │       │   └──────────┘   │
                    │        │         │       │                  │
                    │   S3 Bucket A    │──CCR─│► S3 Bucket B     │
                    └──────────────────┘       └──────────────────┘
                    
                    CCR = Cross-Cluster Replication (跨集群复制)
                    备集群可读不可写, 主集群故障时Promote
```

### 3. 故障处理

| 故障 | 影响 | 处理 |
|------|------|------|
| ES Data Node宕机 | 该节点主分片不可用 | Replica晋升为主分片, 自动重新分配 |
| ES Master宕机 | 集群管理功能暂停 | 剩余Master节点选举新Master |
| Kafka Broker宕机 | 写入临时中断 | Producer自动切换分区, ISR中其他副本接替 |
| 磁盘满 | 写入拒绝 | 索引只读保护, 自动扩容或清理 |
| 查询风暴 | ES响应变慢 | 查询队列限流, Circuit Breaker保护 |

### 4. 监控指标

```
┌──────────────────────────────────────────────────────┐
│                  关键监控指标                          │
├─────────────┬────────────────────────────────────────┤
│ 数据摄入     │ events/s (Kafka input rate)            │
│             │ 数据积压 (Kafka consumer lag)           │
├─────────────┼────────────────────────────────────────┤
│ ES写入       │ indexing rate (docs/s)                │
│             │ indexing latency (P50/P95/P99)         │
│             │ bulk rejections (429 errors)           │
├─────────────┼────────────────────────────────────────┤
│ ES搜索       │ search rate (queries/s)               │
│             │ search latency (P50/P95/P99)           │
│             │ search queue size                      │
├─────────────┼────────────────────────────────────────┤
│ JVM         │ heap usage (< 75% is healthy)          │
│             │ GC frequency & duration                │
│             │ Old GC 频率 (Full GC 应极少)            │
├─────────────┼────────────────────────────────────────┤
│ 操作系统      │ disk I/O utilization                 │
│             │ CPU utilization                        │
│             │ disk space (watermark alarm at 85%)    │
└─────────────┴────────────────────────────────────────┘
```

### 5. 成本优化策略

```
1. 日志采样
   - 正常请求: 100% 记录
   - 成功请求(非慢): 采样率 10%
   - 健康检查: 采样率 1% 或直接过滤

2. 字段裁剪
   - 删除不必要的字段 (如全量stack trace仅保留前100行)
   - 大文本字段不索引 (只存储不搜索)

3. 压缩
   - ES 使用 best_compression (DEFLATE)
   - Kafka 使用 zstd 压缩
   - S3 归档文件使用 gzip + 分块

4. 分层存储
   - Hot: SSD (贵, 快) → 3天
   - Warm: HDD (中等) → 30天
   - Cold: S3 (便宜) → 90天
   - Archive: Glacier (极便宜) → 1年+
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 采集层 | Filebeat/Fluentd 轻量采集, 多源接入 |
| 缓冲层 | Kafka 削峰填谷, 持久化保证数据不丢失 |
| 处理层 | Logstash/Flink 解析+丰富+聚合 |
| 存储层 | Elasticsearch(搜索) + S3(归档) 分层存储 |
| 查询层 | Kibana/Grafana 可视化, Alert Manager 告警 |
| 核心算法 | 倒排索引 + 跳表优化, ILM 生命周期管理 |
| 性能优化 | Bulk写入, Refresh间隔调优, Filter Context缓存 |
| 扩展性 | 节点角色分离, 分片水平扩展, 多数据中心CCR |

**CAP 取舍：** 日志系统选择 AP 模型（可用性 + 分区容错）。日志数据的特点是"宁可丢失少量数据也不能让写入不可用"。Kafka 作为缓冲层保证在 ES 故障时日志数据不会丢失。ES 的写入可用性优先于一致性（通过异步刷新即可搜索）。

**关键设计原则：**
1. 日志通道必须比业务系统更可靠——永远不会因为日志系统故障导致业务中断
2. "写得快, 查得准"——写入路径极简（Kafka直接写入），查询路径丰富（倒排索引+聚合框架）
3. 成本可控——通过分层存储和采样策略，在搜索灵活性和存储成本间取得平衡
