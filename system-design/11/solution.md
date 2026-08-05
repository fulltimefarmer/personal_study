# 设计分布式消息队列 (Design Distributed Message Queue)

## 题目

设计一个分布式消息队列系统，类似 Kafka / RabbitMQ。支持高吞吐量、持久化、可水平扩展的消息发布与订阅。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| 创建Topic | 用户可以创建消息主题 (Topic) |
| 发布消息 | Producer 向指定 Topic 发布消息 |
| 订阅消息 | Consumer 订阅 Topic，以 Consumer Group 方式消费 |
| 消息持久化 | 消息写入磁盘，保证不丢失 |
| 消息顺序 | 在同一个 Partition 内保证消息顺序 |
| 消息回溯 | Consumer 可以重新消费历史消息 (Offset Reset) |
| 消息确认 | Consumer 消费完成后提交 Offset (Commit) |
| 消息过期 | 支持基于时间的消息保留策略 (Retention) |
| 消息过滤 | Consumer 可以按条件过滤消息（可选） |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 吞吐量 | 百万级消息/秒 |
| 延迟 | P99 < 10ms (Producer → Consumer) |
| 可用性 | 99.99% (3个9以上) |
| 持久性 | 消息写入后不可丢失，多副本 |
| 可扩展性 | 水平扩展，增加 Broker 即可提升吞吐量 |
| 一致性 | 强一致或最终一致（取决于配置） |

### 容量估算

假设：
- DAU: 1亿
- 平均每人每天产生 100 条消息
- 每条消息平均 1KB
- 消息保留 7 天

```
日消息量 = 1亿 × 100 = 100亿条/天
QPS (平均) = 100亿 / 86400 ≈ 115,740 QPS
QPS (峰值) = 115,740 × 3 = 347,222 QPS (峰值为平均的3倍)

日写入量 = 100亿 × 1KB = 10TB/天
7天存储 = 10TB × 7 = 70TB
考虑3副本 = 70TB × 3 = 210TB

带宽 = 10TB / 86400 ≈ 926 Mbps (写入)
读写总带宽 ≈ 926 × 3 ≈ 2.8 Gbps
```

---

## API设计

### REST API

```java
// 1. 管理端 API

// 创建 Topic
POST /api/v1/topics
{
  "name": "order_events",
  "partitions": 16,
  "replicationFactor": 3,
  "retentionMs": 604800000,    // 7天
  "maxMessageBytes": 1048576   // 1MB
}

// 获取 Topic 列表
GET /api/v1/topics

// 获取 Topic 详情
GET /api/v1/topics/{topicName}
```

### 生产端 API (Binary Protocol / TCP)

消息队列通常使用自定义二进制协议而非 HTTP，以获得更高吞吐量。

```
// Producer 协议 (类 Kafka Protocol)
ApiKey: 0 (Produce)
Request:
  - transactional_id: String | null
  - acks: int16              // 0=none, 1=leader, -1=all
  - timeout_ms: int32
  - topic_data:
      - topic: String
      - partition_data:
          - partition: int32
          - record_set: RecordBatch (compressed)

Response:
  - throttle_time_ms: int32
  - responses:
      - topic: String
      - partition_responses:
          - partition: int32
          - error_code: int16
          - base_offset: int64
          - log_append_time_ms: int64
```

### 消费端协议

```
// Consumer 协议
ApiKey: 1 (Fetch)
Request:
  - replica_id: int32        // -1 for consumer
  - max_wait_ms: int32
  - min_bytes: int32
  - max_bytes: int32
  - topics:
      - topic: String
      - partitions:
          - partition: int32
          - fetch_offset: int64

Response:
  - throttle_time_ms: int32
  - responses:
      - topic: String
      - partition_responses:
          - partition: int32
          - error_code: int16
          - high_watermark: int64
          - record_set: RecordBatch

// Offset Commit
ApiKey: 8 (OffsetCommit)
Request:
  - group_id: String
  - generation_id: int32
  - member_id: String
  - topics:
      - topic: String
      - partitions:
          - partition: int32
          - offset: int64
          - metadata: String
```

### Consumer Group 管理

```
// JoinGroup — Consumer 加入消费组
ApiKey: 11 (JoinGroup)
Request:
  - group_id: String
  - session_timeout_ms: int32
  - member_id: String
  - protocol_type: "consumer"
  - protocols: [{ name, metadata }]

Response:
  - error_code: int16
  - generation_id: int32
  - protocol_name: String
  - leader_id: String
  - member_id: String
  - members: [{ member_id, metadata }]

// SyncGroup — 分配 Partition
ApiKey: 14 (SyncGroup)
// Heartbeat — 心跳保持
ApiKey: 12 (Heartbeat)
```

---

## 数据模型

### 核心数据结构

```
Topic (逻辑概念)
├── name: "order_events"
├── partitions: [P0, P1, ..., P15]
├── retentionMs: 604800000
└── config: {...}

Partition (物理存储单元)
├── topicName: "order_events"
├── partitionId: 0
├── replicas: [Broker1, Broker2, Broker3]
├── leader: Broker1
├── isr: [Broker1, Broker2]          // In-Sync Replicas
├── firstOffset: 0                   // 最早可读 offset
├── lastOffset: 12345678             // 最新 offset
└── logSegments: [Segment_0, Segment_1, ...]

LogSegment (物理文件)
├── baseOffset: 0
├── size: 1073741824                 // 1GB
├── logFile: "00000000000000000000.log"
├── indexFile: "00000000000000000000.index"
└── timeIndexFile: "00000000000000000000.timeindex"

ConsumerGroup
├── groupId: "order_processor"
├── state: "Stable"                  // Stable | PreparingRebalance | AwaitingSync
├── members: [{ memberId, clientId, assignedPartitions }]
├── generationId: 5
├── offsets: {
│     "order_events-0": 1000,        // topic-partition → committed offset
│     "order_events-1": 950
└── }
```

### 存储引擎设计

```
消息存储结构 (列式, 类似 Kafka):

RecordBatch:
+----------+----------+----------+----------+-----+
| Offset   | Timestamp| Key Size | Key      | ... |
| (8 bytes)| (8 bytes)| (4 bytes)| (var)    |     |
+----------+----------+----------+----------+-----+
     | Val Size  | Value    | Headers    |
     | (4 bytes) | (var)    | (var)      |
     +-----------+----------+------------+

稀疏索引 (Sparse Index) - 每 4KB 记录一个 offset 到物理位置的映射:
IndexEntry:
+----------+----------+
| Offset   | Position |
| (8 bytes)| (4 bytes)|
+----------+----------+

时间索引 (Time Index) - 每 N ms 记录一个 offset 到时间的映射:
TimeIndexEntry:
+----------+----------+
| Offset   | Timestamp|
| (8 bytes)| (8 bytes)|
+----------+----------+
```

### 元数据存储 (ZooKeeper / etcd / KRaft)

```
/msg-queue
├── /brokers
│   ├── /ids
│   │   ├── /0 → {"host":"broker0","port":9092}
│   │   └── /1 → {"host":"broker1","port":9092}
│   └── /topics
│       └── /order_events
│           └── /partitions
│               └── /0/state → {"leader":0, "isr":[0,1], "epoch":3}
├── /consumers
│   └── /order_processor
│       ├── /ids
│       │   └── /consumer-1 → {"subscription": ["order_events"]}
│       ├── /owners
│       │   └── /order_events/0 → "consumer-1"
│       └── /offsets
│           └── /order_events/0 → 1000
└── /controller → {"brokerid": 0}   // Controller 选举
```

---

## 高层次架构

### 系统架构图

```
                        ┌──────────────────────────┐
                        │    Metadata Service       │
                        │  (ZooKeeper / KRaft)      │
                        │                           │
                        │  ┌───────────────────────┐│
                        │  │  Topic/Partition 元数据 ││
                        │  │  Broker 注册/发现      ││
                        │  │  Controller 选举       ││
                        │  │  Consumer Group 状态   ││
                        │  └───────────────────────┘│
                        └───────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Broker 0    │          │   Broker 1    │          │   Broker 2    │
│  (Controller) │◄────────►│               │◄────────►│               │
│               │  数据复制  │               │  数据复制  │               │
│ P0(Leader)    │          │ P1(Leader)    │          │ P2(Leader)    │
│ P1(Follower)  │          │ P0(Follower)  │          │ P0(Follower)  │
│ P3(Leader)    │          │ P2(Follower)  │          │ P1(Follower)  │
│               │          │               │          │               │
└───┬───┬───────┘          └───┬───┬───────┘          └───┬───┬───────┘
    │   │                      │   │                      │   │
    │   ▼                      │   ▼                      │   ▼
    │ 磁盘(SSD)                │ 磁盘(SSD)                │ 磁盘(SSD)
    │                          │                          │
    ▼                          ▼                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Network Layer (TCP)                       │
└──────────────────────────────────────────────────────────────────┘
    │         ▲                 │         ▲                 │
    │         │                 │         │                 │
    ▼         │                 ▼         │                 ▼
┌────────┐ ┌──┴──────┐   ┌────────┐ ┌──┴──────┐   ┌────────┐
│Producer│ │Consumer │   │Producer│ │Consumer │   │Consumer│
│  App   │ │  App    │   │  App   │ │  App    │   │  App   │
└────────┘ └─────────┘   └────────┘ └─────────┘   └────────┘
  Group A   Group B        Group C   Group B        Group A
```

### 数据流

```
=== 消息写入流程 (Write Path) ===

Producer                    Leader Broker           Follower Brokers      Metadata
   │                             │                       │                   │
   │ ① 请求元数据(Topic分区信息)  │                       │                   │
   │─────────────────────────────────────────────────────────────────────►│
   │ ② 返回Leader Broker地址     │                       │                   │
   │◄─────────────────────────────────────────────────────────────────────│
   │                             │                       │                   │
   │ ③ 发送消息(acks=all)        │                       │                   │
   │────────────────────────────►│                       │                   │
   │                             │ ④ 写入本地日志(PageCache)                   │
   │                             │──────► SSD                             │
   │                             │                       │                   │
   │                             │ ⑤ 复制到Follower       │                   │
   │                             │──────────────────────►│                   │
   │                             │                       │ ⑥ 写入本地日志     │
   │                             │                       │──────► SSD       │
   │                             │                       │                   │
   │                             │ ⑦ 收到确认(ACK)        │                   │
   │                             │◄──────────────────────│                   │
   │                             │                       │                   │
   │ ⑧ 返回成功 (Offset)         │                       │                   │
   │◄────────────────────────────│                       │                   │

=== 消息消费流程 (Read Path) ===

Consumer                 Leader Broker              Coordinator
   │                          │                           │
   │ ① 请求消息(Fetch Offset)  │                           │
   │─────────────────────────►│                           │
   │                          │ ② 从PageCache/磁盘读取    │
   │                          │──────► SSD               │
   │ ③ 返回RecordBatch        │                           │
   │◄─────────────────────────│                           │
   │                          │                           │
   │ ④ 处理消息...             │                           │
   │                          │                           │
   │ ⑤ 提交Offset             │                           │
   │─────────────────────────────────────────────────────►│
   │                          │                           │
   │ ⑥ 确认提交成功            │                           │
   │◄─────────────────────────────────────────────────────│
```

### 零拷贝 (Zero-Copy) 数据传输

```
传统方式 (4次拷贝, 2次系统调用):
磁盘 → Read Buffer → 应用Buffer → Socket Buffer → 网卡

零拷贝 sendfile() (2次拷贝):
磁盘 → Read Buffer ──────────────→ Socket Buffer → 网卡
          │                              ▲
          └── DMA Copy ──────────────────┘
```

---

## 核心深入

### 1. 存储引擎设计

#### 顺序写入 vs 随机写入

```
顺序写入性能:
  HDD: ~100-150 MB/s
  SSD: ~500-2000 MB/s

随机写入性能:
  HDD: ~1-2 MB/s (比顺序慢100倍)
  SSD: ~200-500 MB/s (比顺序慢2-4倍)

消息队列采用 Append-Only 顺序写入策略:
  - 新消息始终追加到 Segment 文件末尾
  - 利用 Page Cache + fsync 策略保证持久化
  - 删除操作仅发生在整个 Segment 级别 (Segment 过期后整文件删除)
```

#### Page Cache 策略

```
Kafka 的设计哲学 — 依赖 OS Page Cache 而非 JVM 堆内存:

优势:
  1. GC 压力为零 — 消息数据不在 JVM 堆中
  2. 缓存与 OS 共享 — 利用所有物理内存
  3. 零拷贝 — sendfile() 直接从 Page Cache 传输到网卡
  4. 冷热分离 — OS 自动管理 LRU 淘汰

配置:
  log.flush.interval.messages = 10000   // 每10000条消息刷盘
  log.flush.interval.ms = 1000          // 每1秒刷盘
  
  注意: Kafka 的持久性依赖副本而非 fsync, 
        单个 Broker 可能丢失 Page Cache 中未刷盘的数据,
        但其他副本有完整数据。
```

#### Segment 文件管理

```
Partition 目录结构:
order_events-0/
├── 00000000000000000000.log          # Segment 0 数据文件
├── 00000000000000000000.index        # Segment 0 偏移索引
├── 00000000000000000000.timeindex    # Segment 0 时间索引
├── 00000000000000100000.log          # Segment 1 数据文件
├── 00000000000000100000.index
├── 00000000000000100000.timeindex
└── leader-epoch-checkpoint           # Leader epoch 记录

Segment 切换条件:
  - Segment 文件大小达到 log.segment.bytes (默认 1GB)
  - 时间达到 log.roll.ms (默认 7天)

查找算法 (给定 offset 查找消息):
  1. 二分查找 Segment 列表 (根据 baseOffset)
  2. 在 Segment 的 .index 文件中二分查找 ≤ target offset 的最大索引项
  3. 从索引项记录的物理位置开始顺序扫描，找到目标 offset

时间索引查找 (给定 timestamp 查找消息):
  1. 二分查找 .timeindex 文件，找到 ≤ target timestamp 的最大索引项
  2. 通过索引项中的 offset 跳转到数据文件
```

### 2. 消息可靠性保证

#### Producer 确认机制 (ACKS)

```
acks = 0 (最多一次 / At-Most-Once)
  Producer 不等待任何确认，直接认为发送成功
  延迟: 最低
  可靠性: 最低 (消息可能丢失)
  适用: 日志收集、监控指标等可容忍少量丢失的场景

acks = 1 (至少一次 / At-Least-Once, 默认)
  Leader 写入本地日志后返回确认
  延迟: 中等
  可靠性: 中等 (Leader 宕机未同步到 Follower 的消息会丢失)
  
acks = -1 / all (精确一次 / Exactly-Once)
  Leader 等待所有 ISR 副本同步完成后返回确认
  延迟: 最高
  可靠性: 最高
  需要配合 min.insync.replicas 使用
  min.insync.replicas = 2 表示至少2个副本(含Leader)确认
```

#### ISR (In-Sync Replicas) 机制

```
ISR 管理:
  - ISR = {副本集合中与 Leader 保持同步的副本}
  - Follower 落后时间超过 replica.lag.time.max.ms (默认30s) 则被踢出 ISR
  - Follower 追赶上后自动重新加入 ISR

Leader 选举策略:
  - 优先从 ISR 中选择新 Leader (Unclean Leader Election)
  - unclean.leader.election.enable = false (默认):
    如果 ISR 为空(所有副本都挂了), 宁愿等待也不选非ISR副本
  - unclean.leader.election.enable = true:
    可以从非ISR中选Leader, 但可能丢失消息
  
CAP 权衡:
  - acks=all + min.insync.replicas=replicationFactor: 偏向 CP (强一致)
  - acks=1: 偏向 AP (高可用)
  - unclean leader election = false: 偏向 CP
```

#### 幂等生产 (Idempotent Producer)

```
幂等生产原理:
  - 每个 Producer 分配唯一 Producer ID (PID)
  - 生产者发送每条消息携带 (PID, sequence_number)
  - Broker 记录每个 (PID, TopicPartition) 的最后5个 sequence_number
  - 如果收到重复 sequence_number 的消息, 直接丢弃

配置:
  enable.idempotence = true

事务支持:
  跨多个 Topic 和 Partition 的原子写入:
  {
    producer.initTransactions();
    producer.beginTransaction();
    producer.send(topic1, msg1);
    producer.send(topic2, msg2);
    producer.commitTransaction();
  }
  
  实现: 使用 TransactionCoordinator + __transaction_state 内部 Topic
```

### 3. Consumer Group 重平衡 (Rebalance)

```
=== Rebalance 触发条件 ===
1. Consumer 加入/离开 Consumer Group
2. Topic Partition 数量变化
3. session.timeout.ms 超时 (Consumer 心跳超时)
4. max.poll.interval.ms 超时 (两次 poll 之间超时)

=== Rebalance 流程 (Eager Protocol) ===
                      Coordinator          Consumer1    Consumer2
                          │                    │            │
   ① FindCoordinator      │                    │            │
   ───────────────────────►                    │            │
                          │                    │            │
   ② JoinGroup Request    │                    │            │
                          │◄───────────────────│            │
                          │◄─────────────────────────────────│
                          │                    │            │
   ③ 选出 Group Leader                      │            │
                          │                    │            │
   ④ 返回成员列表                            │            │
                          │───────────────────► GroupLeader│
                          │                    │            │
   ⑤ 执行分区分配策略                        │            │
                          │                    │ (RoundRobin/Range/Sticky)
                          │                    │            │
   ⑥ SyncGroup (提交分配方案)                 │            │
                          │◄───────────────────│            │
                          │◄─────────────────────────────────│
                          │                    │            │
   ⑦ 返回分配结果                            │            │
                          │───────────────────►│            │
                          │─────────────────────────────────►│
                          │                    │            │
   Rebalance 完成, 开始消费新分区             │            │
   ┌──────────────────────┐                   │            │
   │ "Stop The World"     │                   │            │
   │ 期间所有Consumer停止消费                  │            │
   └──────────────────────┘                   │            │
```

#### 分区分配策略

```
1. Range (默认):
   按 Topic 分别分配, 可能导致不均
   Topic A (5分区, 3 Consumer):
     C0: [P0, P1]
     C1: [P2, P3]
     C2: [P4]

2. RoundRobin:
   所有 Topic 的所有 Partition 统一轮询分配, 更均匀
   Topic A[P0,P1], Topic B[P0,P1,P2] (5分区, 3 Consumer):
     C0: [A-P0, B-P1]
     C1: [A-P1, B-P2]
     C2: [B-P0]

3. Sticky (推荐):
   类似 RoundRobin 但优先保持现有分配, 减少不必要的分区迁移
   初始分配后, Consumer 变化时只移动最少的 Partition

4. Cooperative Sticky (增量重平衡, Kafka 2.4+):
   - 不再 "Stop The World"
   - Consumer 分多轮逐步释放和接管 Partition
   - 未移动的 Partition 继续被消费
   - 大幅减少 Rebalance 影响
```

### 4. 消息压缩

```
Producer端压缩 (发送前压缩):

GZIP (默认):
  压缩比: 高 (5-10x)
  CPU开销: 高
  适用: 网络带宽受限

Snappy:
  压缩比: 中等 (2-3x)
  CPU开销: 低
  适用: 对延迟敏感

LZ4:
  压缩比: 中等 (2-3x)
  CPU开销: 极低 (压缩速度最快)
  适用: 高吞吐场景

ZSTD (Kafka 2.1+):
  压缩比: 高 (4-8x)
  CPU开销: 中等
  适用: 存储空间敏感

压缩策略:
  - Broker 不解压, 原样存储压缩后的 RecordBatch
  - Consumer 拉取后解压
  - 减少网络传输量和磁盘存储量
```

### 5. 延迟队列 / 死信队列

```
延迟队列实现:
  - 不同级别的延迟队列:
    delay.q.1s, delay.q.5s, delay.q.10s, delay.q.30s, delay.q.1m, ...
  - 从延迟队列消费, 检查是否到达处理时间
  - 时间到了 → 发给业务队列, 时间未到 → 重新发回延迟队列

死信队列 (DLQ):
  - 消息处理失败超过重试次数后进入 DLQ
  - DLQ 单独保留, 人工处理或定期重放
```

### 6. 监控与运维

```
关键指标:

Broker级别:
  - MessagesInPerSec / BytesInPerSec / BytesOutPerSec
  - TotalProduceRequestsPerSec / TotalFetchRequestsPerSec
  - ActiveControllerCount (应始终为1)
  - OfflinePartitionsCount (应为0)
  - UnderReplicatedPartitions (应为0)
  - ISR Shrink / Expand Rate
  - Request queue size
  - Network processor idle percent
  - Log flush rate and time

Consumer级别:
  - Consumer Lag (消费延迟)
  - RecordsConsumedRate / BytesConsumedRate
  - RecordsLagMax (最大滞后量)
  - Commit Rate / Fetch Rate

Producer级别:
  - RecordSendRate / BytesSendRate
  - RecordErrorRate
  - RequestLatencyAvg / RequestLatencyMax
  - BatchSizeAvg / CompressionRate

JVM (如果使用Java):
  - Heap Memory Usage
  - GC Pause Time
  - Thread Count

告警规则:
  - UnderReplicatedPartitions > 0 持续 5分钟
  - ConsumerLag > 阈值 持续 10分钟
  - ActiveControllerCount ≠ 1 超过 1分钟
  - OfflinePartitionsCount > 0
  - 磁盘使用率 > 85%
```

---

## 扩展性与高可用

### 1. 水平扩展

```
=== Broker 扩容 ===
1. 部署新 Broker 节点
2. 新 Broker 向 Metadata Service 注册
3. 不会自动迁移现有 Partition (避免大规模数据搬迁)
4. 新创建的 Topic 会自动分配 Partition 到新 Broker
5. 如需均衡负载, 使用 Partition Reassignment 工具手动迁移

=== Partition 扩容 ===
1. 使用 Admin API 增加 Partition 数:
   adminClient.createPartitions({"order_events": 32})

警告:
  - Partition 数量只能增加不能减少
  - 增加 Partition 可能破坏基于 Key 的语义
  - 相同 Key 的消息可能被路由到不同的 Partition
```

### 2. 多数据中心 / 跨地域复制

```
=== MirrorMaker 2.0 (Kafka Connect) ===

DC-West (主)                         DC-East (备)
┌───────────┐                      ┌───────────┐
│ Kafka     │═══ MirrorMaker 2.0═══│ Kafka     │
│ Cluster A │                      │ Cluster B │
└───────────┘                      └───────────┘

特性:
  - Offset 同步 (保证迁移后 offset 一致)
  - Topic 配置同步
  - 自动检测新 Topic/Partition
  - 支持双向复制 (Active-Active)
```

### 3. 自动化运维

```
=== Controller (集群控制器) ===
职责:
  - Broker 上下线管理
  - Partition Leader 选举
  - Partition Reassignment
  - 维护 ISR 列表

Controller 选举:
  - 所有 Broker 竞争在 Metadata Service 中创建 /controller 节点
  - 第一个成功创建的成为 Controller (临时节点, session 断开自动删除)
  - 每个 Broker 都有 Controller 功能, 但同一时间只有一个 Active

=== Self-Balancing Cluster (KIP-392) ===
  - 自动检测 Broker 负载不平衡
  - 自动选择最优 Partition 迁移计划
  - 限速迁移, 避免影响正常流量
```

### 4. 灾难恢复

```
=== 灾难场景 ===

场景1: 单Broker故障
  影响: 该Broker上的Leader Partition不可用
  恢复: Controller检测后, 重新在其他Broker上选举Leader
  RTO: <30秒 (Controller检测 + Leader选举)

场景2: Controller故障
  影响: 暂时无法处理元数据变更(已有消息收发不受影响)
  恢复: Metadata Service 检测会话过期, 其他Broker竞争成为新Controller
  RTO: <30秒

场景3: Metadata Service 集群故障
  影响: 无法创建新Topic, Consumer无法Rebalance, 已有连接可能受影响
  恢复: Metadata Service自身的选举和恢复机制
  防: 至少3节点, 分布在不同机架
  
场景4: 整个数据中心故障
  影响: 全面停服
  恢复: DNS/GSLB切换流量到备用数据中心
  防: MirrorMaker 跨DC复制, RPO < 10秒

=== 备份策略 ===
  - 文件系统快照 (定时)
  - MirrorMaker 热备 (实时)
  - Tiered Storage: 旧 Segment 上传到 S3/HDFS 降低存储成本
```

### 5. 与 RabbitMQ 的对比

```
┌──────────────┬──────────────────────┬──────────────────────┐
│    特性      │    Kafka             │    RabbitMQ          │
├──────────────┼──────────────────────┼──────────────────────┤
│ 消息模型     │ 发布/订阅 (Pull)     │ 发布/订阅 (Push/Pull) │
│ 路由         │ Topic → Partition    │ Exchange → Queue     │
│ 消费确认     │ Offset Commit        │ Ack (消息级确认)     │
│ 消息优先级   │ 不支持               │ 支持                 │
│ 消息代理     │ Message Broker       │ Messaging Broker     │
│      (区别)  │ (存储式)             │ (路由式)             │
│ 协议         │ 自定义二进制TCP       │ AMQP(0.9.1/1.0)     │
│ 持久化       │ 磁盘(顺序写)         │ 多种持久化后端       │
│ 消息顺序     │ Partition内有序      │ Queue内有序          │
│ 流处理       │ 内置(Kafka Streams)  │ 不支持               │
│ 典型延迟     │ 个位数ms             │ 亚ms (空队列)        │
│ 典型吞吐     │ 百万/s (单机)        │ 万-十万/s            │
│ 适用场景     │ 流处理/日志/Event Sourcing │ 业务消息/任务分发  │
│ CAP偏向      │ CP (可配置为AP)      │ CP (镜像队列)        │
└──────────────┴──────────────────────┴──────────────────────┘
```

---

## 总结

设计分布式消息队列需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **存储模型** | 顺序写入 + PageCache + Segment管理 → 高吞吐 |
| **副本机制** | ISR + 多副本 + 不同 ACK 级别 → 可靠性弹性 |
| **消费模型** | Pull模型 + Consumer Group + Rebalance → 水平消费扩展 |
| **一致性** | ACKS/ISR 配置 → CP vs AP 选择 |
| **性能优化** | 零拷贝 + 批量处理 + Producer端压缩 + 顺序I/O |
| **元数据** | 外部协调服务 → 集群成员管理和配置 |
| **运维** | Consumer Lag监控 + 自动Rebalance + 分区重分配 |

最关键的面试问答：
1. **为什么 Kafka 这么快？** — 顺序写入 + PageCache + 零拷贝 + 批量处理 + Producer端压缩
2. **如何保证消息不丢失？** — acks=all + min.insync.replicas + 禁用unclean leader election + 幂等/事务Producer
3. **如何保证消息不重复？** — 幂等Producer + 事务 + 唯一ID去重(消费者端)
4. **消息积压怎么办？** — 增加Consumer实例(但不能超过Partition数) + 增加Partition + 调整Consumer处理逻辑
5. **Kafka vs RabbitMQ？** — Kafka主打高吞吐流处理, RabbitMQ主打灵活的业务消息路由
