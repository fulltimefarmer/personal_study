# 题目：Design a Key-Value Store

## 需求澄清（Requirement Clarification）

### 功能需求
1. 支持基本的 KV 操作：`GET(key)`、`PUT(key, value)`、`DELETE(key)`。
2. `GET` 操作要么返回最新写入的值，要么返回「Key 不存在」。
3. `PUT` 操作创建或覆盖已有 Key 对应的 Value。
4. Value 大小范围：1KB ~ 10MB。
5. 支持 TTL（过期时间），Key 到期后自动删除。
6. 高性能：单机 10W+ QPS，集群百万级 QPS。
7. 数据持久化，节点重启后数据不丢失。

### 非功能需求
- **高可用（Availability）**：系统需 24/7 可用，容忍部分节点故障。
- **可扩展性（Scalability）**：支持动态添加/移除节点，数据自动重平衡。
- **低延迟**：P99 读/写延迟 < 5ms。
- **持久性（Durability）**：写入数据在确认后不丢失（WAL + 复制）。
- **CAP 取舍**：根据场景在一致性、可用性、分区容忍性之间做权衡。

### 容量估算
- **日请求量**：峰值 1M QPS，日请求量约 86B。
- **存储量**：假设平均 Value 10KB，存储 500TB 数据，副本 ×3 = 1.5PB。
- **节点规划**：单机 1TB 存储 + 25K QPS，需 500 台存储节点 + 40 台应对 QPS。综合考虑 ≈ 1000-1500 台节点（含副本）。
- **网络带宽**：1M QPS × 平均 12KB（请求 + 响应）≈ 12GB/s 集群内网络流量。

---

## 系统接口（API Design）

### RESTful API

```
# 获取值
GET /api/v1/kv/{key}

Response 200:
{
  "key": "user:1001",
  "value": "{"name":"张三","age":28}",
  "content_type": "application/json",
  "created_at": "2026-07-30T10:00:00Z",
  "ttl_remaining": 3600   // 剩余存活秒数，null 表示永不过期
}

Response 404:
{ "error": "Key not found" }


# 写入/更新值
PUT /api/v1/kv/{key}
Content-Type: application/json

Request:
{
  "value": "{"name":"张三","age":28}",
  "content_type": "application/json",    // 可选
  "ttl": 86400,                           // 可选，秒
  "if_not_exists": true                   // 可选，仅新建
}

Response 201 Created / 200 OK:
{
  "key": "user:1001",
  "status": "ok"
}


# 删除值
DELETE /api/v1/kv/{key}

Response 204 No Content


# 批量获取
POST /api/v1/kv/batch_get

Request:
{ "keys": ["user:1001", "user:1002", "user:1003"] }

Response 200:
{
  "results": [
    { "key": "user:1001", "value": "...", "found": true },
    { "key": "user:1002", "value": null, "found": false },
    { "key": "user:1003", "value": "...", "found": true }
  ]
}
```

### 一致性选项（请求头控制）

```
GET /api/v1/kv/{key}
X-Consistency-Level: quorum    // one / quorum / all

PUT /api/v1/kv/{key}
X-Consistency-Level: quorum
```

- **one**：只要一个节点确认即可（最低延迟，可能读到旧数据）。
- **quorum**：`(N/2 + 1)` 个节点确认（大多数，兼顾一致性与可用性）。
- **all**：所有 N 个节点确认（强一致性，任意节点故障阻塞写入）。

---

## 数据模型（Data Model）

### 单节点存储引擎：LSM-Tree

KV 存储通常在单节点上使用 LSM-Tree（Log-Structured Merge Tree），典型实现如 LevelDB / RocksDB。

| 组件 | 描述 |
|------|------|
| **MemTable** | 内存中的跳表（SkipList），写入先入 MemTable |
| **WAL** (Write-Ahead Log) | 顺序追加日志，保证崩溃恢复 |
| **SSTable** (Sorted String Table) | 磁盘上不可变的排序文件，多层（Level 0 ~ N） |
| **Compaction** | 后台合并 SSTable，清理过期/被覆盖的数据，减少文件数量 |
| **Bloom Filter** | 每层 SSTable 配布隆过滤器，快速判断 Key 是否可能存在 |

### 数据分片模型

```
集群分片视图:
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Node A   │      │ Node B   │      │ Node C   │
│          │      │          │      │          │
│ [0-5460] │      │[5461-1092│      │[10923-   │
│          │      │    2]    │      │ 16383]   │
└──────────┘      └──────────┘      └──────────┘
   ↑                  ↑                  ↑
   │                  │                  │
┌──┴──────────────────┴──────────────────┴──┐
│          一致性哈希环 (0 ~ 2^32-1)          │
│          Hash Slot: 0 ~ 16383              │
└────────────────────────────────────────────┘
```

### 元数据表（集群控制面）

| 字段 | 描述 |
|------|------|
| **Slot 路由表** | 每个 Slot → 负责的节点（主 + 副本）映射 |
| **节点状态** | 在线 / 离线 / 正在加入 / 正在离开 |
| **数据迁移状态** | Slot 迁移中 → 目标节点、迁移进度 |

元数据由 **配置中心（如 etcd / ZooKeeper / Raft 组）** 集中管理，保证一致性。

---

## 架构设计（High-Level Design）

### 整体架构图（ASCII）

```
        ┌─────────────┐
        │   Client    │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ API Gateway │
        └──────┬──────┘
               │
      ┌────────┼────────┐
      │        │        │
┌─────▼──┐ ┌──▼────┐ ┌─▼──────┐
│ Proxy  │ │ Proxy │ │ Proxy  │   ← 路由层（无状态）
│ Node 1 │ │ Node2 │ │ Node 3 │
└───┬────┘ └───┬───┘ └───┬────┘
    │          │         │
    │    ┌─────┴─────┐   │
    │    │           │   │
┌───▼────▼──┐  ┌─────▼───▼──┐  ┌───────────┐
│   Data    │  │   Data     │  │   Data    │
│  Node A   │  │  Node B    │  │  Node C   │
│ (Master)  │  │ (Master)   │  │ (Master)  │
│           │  │            │  │           │
│ RocksDB   │  │ RocksDB    │  │ RocksDB   │
└───────────┘  └────────────┘  └───────────┘
     ▲              ▲               ▲
     │              │               │
┌────┴──────────────┴───────────────┴────┐
│         配置中心 (etcd / Raft)           │
│   - 节点发现                            │
│   - Slot 路由表                         │
│   - 分布式锁                            │
└────────────────────────────────────────┘
```

### 组件职责

| 组件 | 职责 |
|------|------|
| **Client** | SDK 封装：一致性哈希路由计算、请求重试、故障转移 |
| **Proxy Node** | 无状态路由层：接收 Client 请求 → 查询 Slot 路由表 → 转发到正确数据节点 → 聚合结果 |
| **Data Node** | 存储节点：运行 RocksDB 引擎，处理单个 Slot 的读写请求、数据复制、Compaction |
| **配置中心（etcd/Raft）** | 集群元数据存储：节点列表、Slot 分布、Leader 选举；提供 Watch 机制推送路由变更 |
| **监控与告警** | Prometheus 采集 QPS、延迟、磁盘容量、复制 Lag；Grafana 大盘可视化 |

#### 读写流程

**写入流程**：
```
Client → Proxy 计算 Key 的 hash slot
→ Proxy 查路由表获取负责该 slot 的 Data Node（Master）
→ Proxy 转发 PUT 到 Master Data Node
→ Master Node:
   1. 写入 WAL (顺序持久化)
   2. 写入 MemTable (内存)
   3. 异步/同步复制到 Slave 节点
   4. 达到 quorum 后返回 ACK
→ Proxy 返回 ACK 给 Client
```

**读取流程**：
```
Client → Proxy 计算 hash slot → 查路由表
→ 根据一致性级别选择节点:
   - one: 随机选一个可用副本，直接读
   - quorum: 向 ≥ quorum 个副本发起读请求，取最新版本号的值
   - all: 向所有副本读，取最新
→ 返回结果
```

---

## 深入探讨（Deep Dive）

### 1. 一致性哈希（Consistent Hashing）原理与虚拟节点

#### 传统取模分片的问题

假设有 N 个节点，`shard = hash(key) % N`。当节点增减时，N 变化导致几乎所有 Key 需要重新映射。3 节点扩容到 4 节点，约 75% 的数据需要迁移 —— 这在线上是不可接受的。

#### 一致性哈希原理

将节点和 Key 映射到同一个环形哈希空间（0 ~ 2^32 - 1）：

```
                    0
           ┌────────●────────┐
          /                  \
         /                    \
        ●  Node A (hash=A)    ●
       /                        \
      |                          |
      |     哈希环 (Hash Ring)    |
      |                          |
       \                        /
        ●  Node C (hash=C)    ●
         \                    /
          \                  /
           └────────●────────┘
               2^32-1

Key 的路由规则: 从 Key 的哈希位置顺时针找到第一个 Node
```

- **新增节点**：只需将相邻节点的部分数据迁移到新节点。
- **移除节点**：将其数据顺时针移到下一个节点。
- **影响范围**：仅影响相邻节点，而非全局。

#### 虚拟节点（Virtual Nodes）

**问题**：物理节点少时，环形上节点分布不均匀，导致数据倾斜（部分节点负载过高）。

**解决方案**：每个物理节点映射为多个虚拟节点（如 150 个），散布在哈希环上：

```
物理节点 A → 虚拟节点 A0, A1, A2, ..., A149（均匀分布在整个环上）
物理节点 B → 虚拟节点 B0, B1, B2, ..., B149
物理节点 C → 虚拟节点 C0, C1, C2, ..., C149
```

- 虚拟节点越多，数据分布越均匀。
- 增减物理节点时，虚拟节点的迁移更细粒度。
- 可用虚拟节点分配不同权重：性能强的机器分配更多虚拟节点（`vnode_count ∝ capacity`）。

#### 数据迁移方案

移除节点：

```
1. 标记节点为 "待下线"
2. 计算每个虚拟节点顺时针下一个节点，将数据异步复制过去
3. 复制完成后更新路由表，通知所有 Proxy/Client
4. 关闭已下线节点
```

新增节点：

```
1. 新节点加入集群，向配置中心注册
2. 创建虚拟节点映射
3. 从相邻节点 Copy 数据到新节点
4. 更新路由表，路由切换（短暂双写过渡）
5. 相邻节点清理已迁移数据
```

### 2. CAP 定理取舍

#### CAP 回顾

| 属性 | 定义 |
|------|------|
| **Consistency (一致性)** | 所有节点在同一时刻看到相同的数据 |
| **Availability (可用性)** | 每个请求都能得到非错误的响应（不一定是最新数据） |
| **Partition Tolerance (分区容忍性)** | 系统在网络分区发生时仍能继续运行 |

CAP 定理：三者只能同时满足两个。网络分区（P）在分布式系统中是不可避免的，因此实际的选择是 **CP** 或 **AP**。

#### 典型系统取舍

| 系统 | CAP 选择 | 理由 |
|------|----------|------|
| **Redis Cluster** | CP（偏 A） | 主节点不可用时有短暂不可用窗口（选举期间），但多数时间高可用 |
| **Amazon DynamoDB** | AP | 网络分区时各副本独立提供服务，使用向量时钟解决冲突；分区恢复后通过 Read Repair 达到最终一致 |
| **Etcd / ZooKeeper** | CP | 配置系统必须保证强一致性，网络分区时少数节点拒绝服务 |
| **Cassandra** | AP | 高可用优先，多副本可调一致性级别（Quorum 兼顾） |

#### 推荐的 KV 存储 CAP 设计（AP 为主，可调一致性）

- **默认 AP 模式**：高可用优先，容忍最终一致性。写入 quorum 确认，读取 one 副本即可（高性能）。
- **可选 CP 模式**：对一致性要求高的操作（如金融余额），客户端设置 `X-Consistency-Level: quorum/all`，读写都要求多数节点确认。
- **冲突解决**：
  - **Last-Write-Wins (LWW)**：每个 Value 附带时间戳或版本号，最后写入胜出。简单但可能丢失并发更新。
  - **向量时钟 (Vector Clock)**：记录每次更新的节点 + 版本号，可检测并发冲突。客户端或应用层解决冲突。
  - **分布式事务（2PC / Paxos）**：可选的强一致写入，成本高，仅用于必要场景。

### 3. 复制策略

#### 主从复制（Leader-Follower / Master-Slave）

- **写入**：全部由 Master 处理，Master 将 WAL / Binlog 推送到 Slave。
- **读取**：Master + Slave 均可提供读服务（分摊读压力）。
- **故障转移**：Master 宕机时自动将最新 Slave 提升为 Master（Raft 选举或外部协调器）。

#### 多主复制（Multi-Master / Leaderless）

- 每个副本均可接受写入。
- 写入协调者将写入发送到 ≥ W 个副本，读取时需 ≥ R 个副本，满足 `W + R > N` 保证读到自己写的（Quorum 一致性）。
- **优点**：无单点写入瓶颈，更灵活。
- **缺点**：冲突处理复杂，需要向量时钟或 CRDT。

#### 推荐方案：Quorum 读写 + WAL 复制

```
N = 3（总副本数）
W = 2（写入需 2 个副本确认）
R = 2（读取需 2 个副本）

满足: W + R = 4 > N = 3 → Quorum 一致性
```

- 容忍 1 个副本故障（仍有 2 个可写/可读）。
- 对于极高性能要求可降为 `W=1, R=1`（最终一致模式）。

---

## 扩展与高可用

### 水平扩展
- **Slot 重分配**：增加节点时，将部分 Slot 从现有节点迁移到新节点。
- **自动 Rebalance**：当节点负载或容量不均衡时，调度器自动计算并执行 Slot 迁移。
- **在线迁移**：迁移期间短暂双写，保证服务不中断。

### 故障转移（Failover）
- **心跳机制**：所有节点定期向配置中心发送心跳。
- **Master 故障**：配置中心检测心跳超时 → 从该 Master 的 Slave 中选出新 Master（数据最新的优先）→ 更新路由表 → 广播给所有 Proxy。
- **Slave 故障**：Master 继续服务，标记 Slave offline；补充新 Slave 加入同步。
- **数据修复**：Slave 重新上线后，从 Master 同步缺失的数据（增量同步 + 全量校验）。

### 数据备份与恢复
- **RocksDB Snapshot**：对单节点定时生成 Snapshot（如每天凌晨），上传到对象存储。
- **WAL 备份**：持续将 WAL 文件上传到对象存储，实现分钟级恢复点。
- **恢复流程**：
  1. 下载最新的 Snapshot 恢复大部分数据。
  2. 回放 Snapshot 之后的 WAL 日志，恢复到最新状态。
  3. 从其他副本同步可能缺失的数据。

---

## 总结

### 关键设计决策回顾
1. **存储引擎**：RocksDB（LSM-Tree），天然适合写多读少的 KV 场景，支持 Compaction 和 Bloom Filter 加速读。
2. **分片策略**：一致性哈希 + 虚拟节点（如 16384 个 Hash Slot），节点增减时仅迁移部分数据。
3. **CAP 取舍**：默认 AP 高可用，通过 Quorum 策略可调一致性级别。LWW 或向量时钟解决冲突。
4. **复制策略**：一主多从 + Quorum 读写（W + R > N），兼顾可用性与数据可靠性。
5. **高可用**：自适应故障转移（配置中心 Lease + Raft 选主），自动修复宕机节点数据。

### 可能的改进方向
- **支持复杂数据结构**：在 KV 基础上支持 List、Set、Hash 等（类似 Redis）。
- **LSM-Tree 优化**：分级 Compaction 策略优化（如 Tiered Compaction 减少写放大）；支持 Key-Value 分离存储（WiscKey 架构）以降低大 Value 的 Compaction 开销。
- **事务支持**：跨 Key 的分布式事务（Percolator 模型 / 两阶段提交）。
- **多区域部署**：跨数据中心异步复制，实现异地容灾。
- **可观测性**：全链路 Trace（OpenTelemetry），精确到每次 GET/PUT 的各阶段耗时。
