# 36. 设计分布式文件系统 (Distributed File System like HDFS/GFS)

## 题目

设计一个大规模分布式文件系统，支持海量文件存储、高吞吐读写、容错和扩展性。参考 Google File System (GFS) 和 Hadoop HDFS 的设计理念。

---

## 需求澄清

### 功能性需求

- 存储超大文件（GB～TB级别）
- 高吞吐量的流式读取（适合大数据分析场景）
- 文件追加写入（append-only）
- 文件和目录的创建、删除、重命名
- 访问权限控制
- 数据自动分块（chunk）并分布存储
- 数据冗余和自动故障恢复
- 存储节点自动发现和注册

### 非功能性需求

| 指标 | 要求 |
|------|------|
| 容量 | 支持 PB 甚至 EB 级别 |
| 吞吐 | 聚合读吞吐 > 100GB/s |
| 可用性 | 99.99%，自动故障恢复 |
| 数据持久性 | 副本数≥3，跨机架/数据中心 |
| 一致性 | 强一致性元数据，弱一致性数据(追加) |
| 延迟 | 适合高吞吐而非低延迟场景 |

### 容量估算

假设：
- 总存储需求：100PB
- 平均文件大小：100MB
- 文件数量：100PB / 100MB ≈ 10亿个文件
- 元数据（每个file约 200B）：10亿 × 200B ≈ 200GB
- Chunk大小：64MB
- 总Chunk数：100PB / 64MB ≈ 156万个Chunk
- 副本因子：3 → 实际存储：300PB

---

## 架构设计

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              Clients                                      │
│                    (HDFS Client / GFS Client)                             │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Master (NameNode)                                 │
│                                                                          │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────────────────────┐ │
│  │ Namespace  │  │ Block/Chunk  │  │  Lease Manager                  │ │
│  │ Manager    │  │ Location Map │  │  互斥写锁, 租约管理              │ │
│  │            │  │              │  │                                  │ │
│  │ /home/     │  │ chunk_001 →  │  │  file → lease holder            │ │
│  │ /tmp/      │  │   CS1,CS2,CS3│  │  lease → timeout                │ │
│  │ /data/     │  │ chunk_002 →  │  │                                  │ │
│  │            │  │   CS4,CS5,CS6│  │                                  │ │
│  └────────────┘  └──────────────┘  └─────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                Operation Log (Edit Log) + Checkpoint               │   │
│  │                                                                  │   │
│  │  Edit Log: 顺序记录所有元数据变更操作 (WAL)                        │   │
│  │  [CREATE /data/file1] [ADD_CHUNK file1 chunk_001] ...             │   │
│  │                                                                  │   │
│  │  Checkpoint (FsImage): 定期快照内存状态 → 恢复加速                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             │ Heartbeat (每3秒)
                             │ Block Report (每一小时 + 启动时)
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    ChunkServers (DataNodes) - Store Chunks                │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ ChunkServer 1│  │ ChunkServer 2│  │ ChunkServer N│                  │
│  │ Rack 1       │  │ Rack 2       │  │ Rack M       │                  │
│  │              │  │              │  │              │                  │
│  │ /data/disk1/ │  │ /data/disk1/ │  │ /data/diskK/ │                  │
│  │   chunk_001  │  │   chunk_001  │  │   chunk_003  │  (副本)          │
│  │   chunk_004  │  │   chunk_002  │  │   chunk_005  │                  │
│  │   chunk_007  │  │   chunk_006  │  │   chunk_008  │                  │
│  │ /data/disk2/ │  │ /data/disk2/ │  │ /data/disk2/ │                  │
│  │   chunk_010  │  │   chunk_003  │  │   chunk_001  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                          │
│  Chunk Server核心操作:                                                    │
│    - Read(chunk_id, offset, length) → data                              │
│    - Write/Append(chunk_id, data) → ACK                                 │
│    - Replicate to peer chunkservers (pipeline)                          │
│    - Checksum verification (每个64KB块一个CRC32校验)                      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       Standby Master (Secondary NameNode)                 │
│  持续同步Edit Log, 故障时接管                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心深入

### 1. 元数据设计

```
Master (NameNode) 内存数据结构:

┌─────────────────────────────────────────────────────────────┐
│                       File Namespace                        │
│                                                             │
│  /data/ (dir)                                               │
│  ├── logs/ (dir)                                            │
│  │   ├── 2024-01-01.log → [chunk_1001, chunk_1002]          │
│  │   └── 2024-01-02.log → [chunk_1003, chunk_1004]          │
│  └── analysis/ (dir)                                        │
│      └── report.parquet → [chunk_2001, ..., chunk_2020]     │
│                                                             │
│  Namespace = HashMap<FilePath, INode>                        │
│  INode = FileInode { chunks: [ChunkId], replication: 3 }   │
│       |  DirectoryInode { children: [FilePath] }            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Chunk Location Map                      │
│                                                             │
│  chunk_1001 → [CS-rack1-node1, CS-rack2-node5, CS-rack3-n2] │
│  chunk_1002 → [CS-rack2-node3, CS-rack1-node2, CS-rack3-n4] │
│  chunk_1003 → [CS-rack3-node1, CS-rack1-node3, CS-rack2-n1] │
│  ...                                                        │
│                                                             │
│  副本放置策略:                                               │
│    Replica 1: 写入客户端同机架 (或随机)                       │
│    Replica 2: 不同机架的节点                                  │
│    Replica 3: 与Replica 2同机架的不同节点                     │
│    原因: 跨机架容错 + 网络带宽优化                             │
└─────────────────────────────────────────────────────────────┘

Edit Log (顺序日志, 类似WAL):
  Operation Log:
  ┌────┬──────────┬──────────────────────────────┐
  │ Seq│ Operation│        Parameters             │
  ├────┼──────────┼──────────────────────────────┤
  │  1 │ CREATE   │ /data/logs/2024-01-01.log    │
  │  2 │ ADD_CHUNK│ file=/data/logs/... chunk_1001│
  │  3 │ ADD_CHUNK│ file=/data/logs/... chunk_1002│
  │  4 │ CLOSE_FILE│ /data/logs/2024-01-01.log   │
  │  5 │ DELETE   │ /tmp/expired_file.parquet    │
  │ ...│ ...      │ ...                          │
  └────┴──────────┴──────────────────────────────┘

恢复流程:
  Master重启 → 加载最近Checkpoint → 重放Checkpoint之后的Edit Log
```

### 2. 写入流程

```
写入流程 (HDFS/GFS):

Client                         Master                    ChunkServers
  │                               │                         │
  │ 1. create("/data/file")       │                         │
  │──────────────────────────────>│                         │
  │                               │ 检查权限, 创建INode      │
  │                      ┌────────┴────────┐               │
  │                      │ 分配新chunk_id   │               │
  │                      │ 选择3个ChunkServer│              │
  │                      │ (考虑机架、磁盘)  │               │
  │                      └────────┬────────┘               │
  │ 2. 返回chunk_id + CS列表      │                         │
  │<──────────────────────────────│                         │
  │                               │                         │
  │ 3. Data Pipeline Write       │                         │
  │ ─────────────────────────────│                         │
  │   ┌──────────────────────────┼──────────────────┐      │
  │   │ Pipeline写入:            │                  │      │
  │   │ Client → CS1 → CS2 → CS3│                  │      │
  │   │                        │                  │      │
  │   │ Client切chunk为packet   │                  │      │
  │   │ (packet=64KB)          │                  │      │
  │   │                        │                  │      │
  │   │ 4. 发送packet到CS1     │                  │      │
  │   │────────────────────────> CS1 接收并存储     │      │
  │   │                        │──> CS1→CS2转发    │      │
  │   │                        │──────> CS2→CS3转发│      │
  │   │                        │                  │      │
  │   │ 5. ACK沿管道反向返回    │                  │      │
  │   │←─────────────────────────── CS3→CS2→CS1   │      │
  │   └───────────────────────────────────────────┘      │
  │                               │                         │
  │ 6. Chunk写满(64MB)后通知Master│                         │
  │──────────────────────────────>│                         │
  │                               │ 更新ChunkMap             │
  │                               │ 写Edit Log              │
```

**Pipeline Write 为什么比并行副本写入更优？**

| Write Mode | Bandwidth | Complexity |
|------------|-----------|------------|
| Client→CS1, Client→CS2, Client→CS3 | 需要3x上行带宽 | Low |
| **Client→CS1→CS2→CS3** (Pipeline) | **仅需1x上行带宽** | **Medium** |

### 3. 读取流程

```
读取流程:

Client                         Master                    ChunkServers
  │                               │                         │
  │ 1. open("/data/file")         │                         │
  │──────────────────────────────>│                         │
  │                               │ 2. 查Namespace→获取chunk列表
  │                               │    Chunk Location→按网络拓扑排序
  │                               │    (优先返回最近CS)     │
  │ 3. 返回chunk列表 + CS位置      │                         │
  │<──────────────────────────────│                         │
  │                               │                         │
  │ 4. Read(chunk_id, offset, len)│                         │
  │──────────────────────────────────────────────────────>│ CS1 (最近)
  │                               │                         │
  │ 5. Data Stream               │                         │
  │<══════════════════════════════════════════════════════│ CS1
  │                               │                         │
  │ 6. Checksum Verification     │                         │
  │   (客户端验证每个packet的CRC)  │                         │
  │   如果校验失败→重试其他CS副本   │                         │
  │                               │                         │
  │ 7. 如果CS1故障→切换到CS2读取   │                         │
```

### 4. Append 写入（GFS 核心特性）

```
为什么是 Append-Only?

┌─────────────────────────────────────────────────────────────┐
│ 场景: 多个Client并发追加日志到同一文件                        │
│                                                             │
│ 传统方案: 需要分布式锁→复杂, 性能差                           │
│ GFS方案: Atomic Append → 原子追加, 服务端分配offset          │
│                                                             │
│ 流程:                                                       │
│   Client A: append("record_a\n")                            │
│   Client B: append("record_b\n")                            │
│                                                             │
│   Master: 分配chunk + offset, 串行化append请求               │
│   ChunkServer:                                              │
│     1. 设置primary副本                                     │
│     2. Primary决定实际写入偏移量                            │
│     3. Primary写入→Pipeline到其他副本                       │
│     4. 如果写入失败(4096字节写不下)→填充空白 → 通知Client重试│
│     5. 返回实际写入的offset给Client                         │
│                                                             │
│  结果文件:                                                   │
│  0       4096         8192         12288                   │
│  ├─────────┼────────────┼─────────────┤                    │
│  │record_a │  record_b   │ (padding)  │                    │
│  └─────────┴────────────┴─────────────┘                    │
│                                                             │
│  特点: 至少一次语义 (At-Least-Once)                          │
│  可能的冗余: 失败重试可能导致重复记录 (应用层去重)            │
│                                                             │
│  一致性模型:                                                │
│    - 普通写入: 一致但可能未定义(interleave)                   │
│    - Append:  一致且已定义(defined)                          │
│    - 失败:    不一致(不同副本可能不同长度)                    │
└─────────────────────────────────────────────────────────────┘
```

### 5. 租约（Lease）机制

```
租约管理:

┌─────────────────────────────────────────────────────────────┐
│ 对于每个正在写入的Chunk, Master授予一个ChunkServer "租约"     │
│                                                             │
│  Primary ChunkServer (持有租约):                              │
│   - 决定所有副本的写入顺序                                    │
│   - 维护写入操作的序列化                                      │
│   - 租约有效期: 60秒                                        │
│   - 通过心跳续期                                             │
│                                                             │
│  租约失效处理:                                                │
│   - Master检测到租约过期→撤销并重新分配                       │
│                                                             │
│  租约作用:                                                    │
│   1. 减少Master参与每次写入操作的负载                         │
│   2. 提供写入一致性保证                                      │
│   3. 控制并发写入的序列化点                                  │
└─────────────────────────────────────────────────────────────┘
```

### 6. 数据完整性校验

```
Checksum 策略:

┌─────────────────────────────────────────────────────────────┐
│ 每个Chunk被切分为64KB的Block, 每个Block有独立的32位CRC校验和  │
│                                                             │
│ Chunk布局 (64MB):                                            │
│ ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐         │
│ │Block0│Block1│Block2│ ...  │ ...  │ ...  │BlkN  │         │
│ │ 64KB │ 64KB │ 64KB │      │      │      │ 64KB │         │
│ ├──────┼──────┼──────┼──────┼──────┼──────┼──────┤         │
│ │ CRC0 │ CRC1 │ CRC2 │ ...  │ ...  │ ...  │ CRCN │         │
│ └──────┴──────┴──────┴──────┴──────┴──────┴──────┘         │
│                                                             │
│ 校验时机:                                                    │
│  写入时: ChunkServer计算并持久化校验和                        │
│  读取时: Client验证校验和                                    │
│  定期检查: ChunkServer后台扫描所有Chunk验证校验和             │
│                                                             │
│ 校验失败处理:                                                │
│  1. Client使用另一副本重读                                    │
│  2. 上报Master: 该副本损坏                                   │
│  3. Master从其他副本克隆替换损坏副本                          │
└─────────────────────────────────────────────────────────────┘
```

### 7. 数据块报告与副本管理

```
Block Report 机制:

┌─────────────────────────────────────────────────────────────┐
│ ChunkServer向Master报告其存储的所有Chunk                      │
│                                                             │
│ 心跳 (Heartbeat): 每3秒一次                                  │
│   - 报告节点存活                                             │
│   - 报告可用磁盘空间                                         │
│   - 报告正在进行的操作                                       │
│                                                             │
│ Block Report: 每小时一次 + 启动时立即报告                     │
│   - 报告所有Chunk ID列表                                     │
│   - Master检查:                                              │
│     ✓ 哪些Chunk副本不够 → 触发复制                            │
│     ✓ 哪些Chunk副本过多 → 触发删除                            │
│     ✓ 哪些Chunk有损坏副本 → 触发替换                          │
│                                                             │
│ 副本管理 (Re-replication Pipeline):                          │
│                                                                       │
│  当Master发现某Chunk副本数 < target (如只有2/3):                        │
│                                                                       │
│   1. 选择新的ChunkServer作为目标                                        │
│                                                                       │
│   2. 从已有副本复制: Source CS → Pipeline → Target CS                  │
│                                                                       │
│   3. 优先级队列:                                                       │
│                                                                       │
│     Priority 1: 副本数=1 (随时可能丢失)                                  │
│                                                                       │
│     Priority 2: 副本数=2 (低于目标)                                     │
│                                                                       │
│     Priority 3: 重新均衡 (Rebalance)                                   │
└───────────────────────────────────────────────────────────────────────┘
```

### 8. 小文件问题与解决方案

```
HDFS小文件问题:

┌───────────────────────────────────────────────────────────────────────┐
│ 问题: 1亿个小文件(1KB each)                                            │
│   → 1亿 × 200B(每个文件的NameNode内存) ≈ 20GB NameNode内存            │
│   → 1亿 × 2(至少2块元数据) = 2亿Block条目 → 内存压力巨大               │
│                                                                       │
│ 解决方案:                                                              │
│                                                                       │
│ 1. HAR (Hadoop Archive): 小文件打包成 .har, 作为整体访问               │
│                                                                       │
│ 2. SequenceFile / Avro: 小记录合并成大文件, 配合MapReduce              │
│                                                                       │
│ 3. HBase: 小记录存HBase(HFile底层在HDFS), 适合随机读写                 │
│                                                                       │
│ 4. Ozone (对象存储): 新一代存储, 支持数十亿文件                        │
│                                                                       │
│ 5. Federated NameNode: 多个NameNode, 每个管理部分命名空间              │
│    /data/ns1/ → NameNode-1                                           │
│    /data/ns2/ → NameNode-2                                           │
│                                                                       │
│ 方案对比:                                                              │
│ ┌──────────────┬──────────┬──────────┬──────────┐                     │
│ │ 方案          │ 复杂度   │ 访问   │ 适用场景  │                     │
│ │              │          │ 性能   │          │                     │
│ ├──────────────┼──────────┼──────────┼──────────┤                     │
│ │ HAR          │ 低       │ 低      │ 归档     │                     │
│ │ SequenceFile │ 低       │ 中      │ 批处理   │                     │
│ │ HBase        │ 高       │ 高      │ 实时访问 │                     │
│ │ Federation   │ 中       │ 高      │ 通用     │                     │
│ └──────────────┴──────────┴──────────┴──────────┘                     │
└───────────────────────────────────────────────────────────────────────┘
```

### 9. 垃圾回收（Garbage Collection）

```
GFS/HDFS 垃圾回收:

┌───────────────────────────────────────────────────────────────────────┐
│ 删除不是立即的:                                                        │
│                                                                       │
│  1. Client发起DELETE操作                                              │
│                                                                       │
│  2. NameNode:                                                         │
│     - 记录DELETE到Edit Log                                            │
│     - 将文件重命名为隐藏名称 (如 /data/.Trash/file_name)               │
│     - 设置删除时间戳                                                   │
│                                                                       │
│  3. 垃圾回收检查 (定期):                                                │
│     - 检查隐藏文件中超过保留期(如7天)的                                  │
│     - 从Namespace中移除 → 回收Chunk → ChunkServer释放空间               │
│                                                                       │
│  4. Stale Replica 检测:                                                │
│     - ChunkServer遗漏一些Chunk在Block Report中 → 标记为过期             │
│     - Master在某次心跳回复中通知CS清理                                  │
│                                                                       │
│  过期副本清理:                                                          │
│  ┌─────────────────────────┐                                          │
│  │ Version Vector         │  每个Chunk有版本号                         │
│  │ Master知道最新版本      │  ChunkServer有旧版本 → 过期               │
│  └─────────────────────────┘                                          │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 高可用与容错

### 1. NameNode HA

```
NameNode 高可用 (HDFS HA):

┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ┌───────────────────┐         ┌───────────────────┐                  │
│  │ Active NameNode   │         │ Standby NameNode  │                  │
│  │                   │         │                   │                  │
│  │ - 处理所有客户端请求│         │ - 读取共享Edit Log │                  │
│  │ - 写Edit Log      │         │ - 更新内存状态      │                  │
│  │ - 管理ChunkServer │         │ - 等待接管         │                  │
│  │ - 写FsImage       │         │ - 写FsImage        │                  │
│  └────────┬──────────┘         └────────┬──────────┘                  │
│           │                             │                             │
│           └──────────┬──────────────────┘                             │
│                      │                                                │
│                      ▼                                                │
│           ┌─────────────────────┐                                     │
│           │ Quorum Journal      │                                     │
│           │ Manager (QJM)       │  ← 基于Paxos/Raft的共享Edit Log     │
│           │                     │                                     │
│           │ JournalNode 1       │                                     │
│           │ JournalNode 2       │  (至少3个, 写Quorum ≥ 2)            │
│           │ JournalNode 3       │                                     │
│           └─────────────────────┘                                     │
│                      │                                                │
│                      ▼                                                │
│           ┌─────────────────────┐                                     │
│           │ ZooKeeper           │  ← Leader Election + Failover       │
│           │ - 选主               │     Detector                       │
│           │ - 锁                 │                                     │
│           │ - Fencing           │                                     │
│           └─────────────────────┘                                     │
└───────────────────────────────────────────────────────────────────────┘

Fencing (防止脑裂):
  1. Active NameNode失去ZK连接
  2. Standby 晋升为 Active (获取分布式锁)
  3. 新Active通知QJM增加 Epoch Number
  4. 旧Active的任何写操作都会被QJM拒绝(Epoch不匹配)
  5. 新Active执行Fencing: SSH到旧节点Kill NameNode进程
```

### 2. 故障处理矩阵

| 故障 | 影响 | 恢复 |
|------|------|------|
| ChunkServer宕机 | 部分Chunk副本减少 | NameNode检测心跳超时→自动复制到其他CS |
| 磁盘故障 | 部分Chunk丢失 | NameNode检测Block Report中的缺失→复制 |
| NameNode宕机 | 文件系统不可用 | ZK自动Failover到Standby(< 30s) |
| 网络分区 | ChunkServer无法通信 | Client直接连接CS(无需NameNode)，写入需要Master时阻塞 |
| 数据损坏 | 读取失败 | Client读取另一个副本，Master修复损坏副本 |
| Edit Log损坏 | 元数据不一致 | 恢复最近Checkpoint + QJM法定数量日志 |

### 3. 缓存策略

```
HDFS 缓存:

┌───────────────────────────────────────────────────────────────────────┐
│ Centralized Cache Management (集中式缓存管理):                         │
│                                                                       │
│  Cache Directive: 用户可以指定缓存某些文件/目录                        │
│                                                                       │
│  Cache Pool: 管理缓存资源                                              │
│    - pool: analytics_cache (max: 200GB)                              │
│    - pool: realtime_cache  (max: 50GB)                               │
│                                                                       │
│  缓存实现:                                                             │
│    - NameNode管理哪些Chunk被缓存在哪些CS                               │
│    - CS使用OS buffer cache (mmap/mlock)                              │
│    - Read from Cache: 零拷贝(zero-copy)直接发送                       │
│    - 节点重启: 缓存丢失, NameNode重新调度预热                         │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 总结

| 维度 | 设计要点 |
|------|----------|
| 架构 | Master/Slave: NameNode(元数据) + DataNode(数据) |
| 数据组织 | 大Chunk(64MB/128MB) + 多副本(默认3) |
| 一致性 | Master强一致(Edit Log), 数据最终一致(纯追加) |
| 写入 | Pipeline Write + Lease + Atomic Append |
| 读取 | 就近读 + Checksum验证 + 网络拓扑感知 |
| 高可用 | NameNode HA(ZK+QJM), DataNode自动故障恢复 |
| 适用场景| 大文件, 批处理, 高吞吐, 追加写 |

**CAP 取舍:** 分布式文件系统是 **CP** 系统（一致性 + 分区容错）。当发生网络分区时，NameNode 需要多数派(QJM Quorum)才能接受写入操作。如果 NameNode 不能联系到多数 JournalNodes，文件系统将进入只读模式以保护元数据一致性。数据层(ChunkServer)则是AP——读取优先返回可用的副本。

**为什么选择大Chunk设计(64MB)?**
1. 减少NameNode元数据量（元数据大小 ∝ Chunk数）
2. 减少网络往返（一次读写大量数据）
3. 减少客户端与Master的交互（一次查询更多数据）
缺点: 小文件存储效率低，可能产生内部碎片
