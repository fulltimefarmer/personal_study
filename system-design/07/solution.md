# 07. 设计键值存储 (Design a Key-Value Store)

## 题目

设计一个类似 Redis / DynamoDB 的分布式键值存储系统。支持基本的 GET/PUT/DELETE 操作，具有高可用性、可扩展性和低延迟。可深入讨论一致性模型、复制策略、数据分片和故障恢复。

---

## 需求澄清

### 功能性需求

1. **基本操作**：GET(key), PUT(key, value), DELETE(key)
2. **多数据类型**：字符串、列表、集合、有序集合、哈希（取决于定位：缓存型 vs 持久化型）
3. **TTL (过期时间)**：键值对可设置过期时间，到期自动删除
4. **原子操作**：INCR/DECR（计数器）、CAS（Compare-And-Swap）
5. **批量操作**：MGET, MSET, 事务 (MULTI/EXEC)
6. **Pub/Sub（可选）**：发布/订阅消息模式
7. **持久化（可选）**：数据持久化到磁盘 vs 纯内存存储

### 非功能性需求

1. **低延迟**：GET/PUT 操作 < 1ms（P99 < 5ms）
2. **高吞吐量**：单节点 > 100K QPS；集群 > 10M QPS
3. **高可用**：99.99%+ 可用性
4. **可扩展**：支持水平扩展（增加节点自动负载均衡）
5. **容错**：单节点故障不影响整体系统
6. **数据持久性**：根据定位（缓存 vs 持久化存储）不同要求
7. **一致性模型**：支持可配置的一致性级别

### 容量估算

**假设条件（大规模缓存场景）：**
- 总 KV 对数量: 100 亿 (10B)
- 平均 Key 大小: 64 bytes
- 平均 Value 大小: 512 bytes
- 读取 QPS: 10M（峰值 20M）
- 写入 QPS: 1M（峰值 2M）
- 读写比: 10:1

**存储估算：**
- 每 KV 对原始大小: 64B + 512B = 576B
- 加上元数据开销（过期时间、类型标记等）: ~100B
- 总数据大小: 10B × 676B ≈ **6.76 TB**
- 考虑 3 副本: 6.76 TB × 3 ≈ **20.28 TB**
- 内存需求（纯内存型）: 每节点 256GB → 需要约 80 个节点

**网络带宽估算：**
- 出站: 10M QPS × 512B (value) ≈ 5.12 GB/s = **41 Gbps**
- 入站: 1M QPS × 576B ≈ 576 MB/s = **4.6 Gbps**
- 副本同步带宽: 1M QPS × 576B × (N-1)副本 ≈ 1.15 GB/s = **9.2 Gbps**（双副本）

---

## API 设计

### 核心 API

```
1. GET - 读取键值
GET /kv/v1/{key}

Response: 200 OK
{
  "key": "user:12345:name",
  "value": "张三",
  "version": 42,           // 版本号 (用于 CAS)
  "ttl_remaining_ms": 3600000,
  "metadata": {
    "type": "string",
    "created_at": 1704067200000,
    "last_accessed": 1704070800000
  }
}

Response: 404 Not Found

2. PUT - 写入键值
PUT /kv/v1/{key}
Content-Type: application/json

Request:
{
  "value": "张三",
  "ttl_ms": 7200000,          // 可选，过期时间
  "expected_version": 41,     // 可选，CAS 乐观锁
  "nx": false                 // 可选，仅当 key 不存在时写入
}

Response: 201 Created / 200 OK
{
  "key": "user:12345:name",
  "version": 42,
  "created": true
}

Response: 409 Conflict (版本冲突)

3. DELETE - 删除键值
DELETE /kv/v1/{key}?version=42

Response: 204 No Content
Response: 409 Conflict (版本冲突)

4. MGET - 批量读取
POST /kv/v1/mget
{
  "keys": ["key1", "key2", "key3"]
}

Response:
{
  "results": [
    {"key": "key1", "value": "val1", "version": 1},
    {"key": "key2", "value": null, "error": "NOT_FOUND"},
    {"key": "key3", "value": "val3", "version": 5}
  ]
}

5. INCR - 原子递增
POST /kv/v1/{key}/incr
{
  "delta": 1,
  "initial": 0              // 如果 key 不存在，先初始化为这个值
}

Response: 200 OK
{
  "key": "page:count",
  "value": 42
}
```

### 一致性级别配置

```
读取一致性级别 (Read Consistency Level):

- CONSISTENCY_ONE:     从一个节点读取，最快，可能读到旧数据
- CONSISTENCY_QUORUM:  从多数节点 (R+W > N) 读取，强一致
- CONSISTENCY_ALL:     从所有节点读取，最严格，容错性最低

写入一致性级别 (Write Consistency Level):

- CONSISTENCY_ONE:     写入一个节点即返回，最快，可能丢失
- CONSISTENCY_QUORUM:  写入多数节点，强一致
- CONSISTENCY_ALL:     写入所有节点，最严格，最慢

请求头示例:
GET /kv/v1/key1
X-Consistency-Level: QUORUM
```

---

## 数据模型

### 内存数据结构

```c
// 内存中的 KV 条目结构
struct KVEntry {
    char *key;          // 键
    int key_len;        
    void *value;        // 值
    int value_len;
    int type;           // STRING, LIST, SET, HASH, ZSET
    int64_t version;    // 版本号 (CAS)
    int64_t expire_at;  // 绝对过期时间 (毫秒时间戳, 0=永不过期)
    int64_t created_at;
    int64_t last_accessed;
    
    // LRU 链表的双向指针
    struct KVEntry *lru_prev;
    struct KVEntry *lru_next;
};

// 哈希表 (主索引)
// 使用链式哈希(Chaining)或开放寻址(Open Addressing)
// Redis 使用渐进式 rehash 的链式哈希
```

### 持久化格式

```
RDB (Redis Database) 快照:
  二进制格式的时间点快照
  优点: 紧凑、恢复速度快
  缺点: 可能丢失最后一次快照后的数据

AOF (Append-Only File):
  记录每个写操作命令到日志文件
  优点: 数据更安全 (可配置 fsync 策略)
  缺点: 文件大、恢复慢
  
混合持久化 (Redis 4.0+):
  RDB 快照 + AOF 增量
  快照: 子进程 fork 时将当前数据写入 RDB
  增量: 快照期间的写操作写入 AOF 缓冲区
  恢复: RDB 加载 + AOF 重放
```

```python
# AOF 日志格式 (Append-Only File)
# 每条记录: [长度] 操作类型 key value expire

AOF_ENTRY_PUT = 0x01
AOF_ENTRY_DEL = 0x02
AOF_ENTRY_INCR = 0x03
AOF_ENTRY_EXPIRE = 0x04

class AOFWriter:
    def append_put(self, key, value, expire_at, version):
        entry = struct.pack('!B', AOF_ENTRY_PUT)
        entry += self._encode_len_str(key)
        entry += self._encode_len_str(value)
        entry += struct.pack('!q', expire_at or 0)
        entry += struct.pack('!q', version)
        self.fd.write(entry)
        self._check_fsync()

    def _check_fsync(self):
        # fsync 策略: always | everysec | no
        if self.fsync_policy == 'always':
            os.fsync(self.fd)
        elif self.fsync_policy == 'everysec':
            if time.time() - self.last_fsync >= 1:
                os.fsync(self.fd)
                self.last_fsync = time.time()
```

---

## 高层次架构

```
                              ┌──────────────────────────────────────────────┐
                              │               Client (SDK / CLI)              │
                              │    - 一致性哈希路由                            │
                              │    - 多副本写入                                │
                              │    - 故障转移                                  │
                              └─────────────────────┬────────────────────────┘
                                                    │
                              ┌─────────────────────▼────────────────────────┐
                              │              Cluster Manager                  │
                              │                                              │
                              │  ┌──────────────────────────────────────────┐│
                              │  │  Gossip Protocol (成员发现 & 故障检测)      ││
                              │  │  - 节点增删发现                             ││
                              │  │  - 心跳/探活 (PING-PONG)                    ││
                              │  │  - 传播元数据 (拓扑、token/range)            ││
                              │  └──────────────────────────────────────────┘│
                              │                                              │
                              │  ┌──────────────────────────────────────────┐│
                              │  │  Token Ring / Consistent Hashing          ││
                              │  │  - 每个节点持有 token range               ││
                              │  │  - Key → hash → token → 节点映射           ││
                              │  └──────────────────────────────────────────┘│
                              └──────────────────────────────────────────────┘
                                                    │
          ┌─────────────────────────────────────────┼──────────────────────────┐
          │                                         │                          │
┌─────────▼──────────┐                   ┌─────────▼──────────┐    ┌─────────▼──────────┐
│  Storage Node 1    │                   │  Storage Node 2    │    │  Storage Node N    │
│                    │                   │                    │    │                    │
│ ┌────────────────┐ │                   │ ┌────────────────┐ │    │ ┌────────────────┐ │
│ │ In-Memory      │ │                   │ │ In-Memory      │ │    │ │ In-Memory      │ │
│ │ Hash Table     │ │◀────── Replication ──▶│ Hash Table     │ │    │ │ Hash Table     │ │
│ │ (primary dict) │ │        (Async/    │ │ (primary dict) │ │    │ │ (primary dict) │ │
│ │                │ │         Sync)    │ │                │ │    │ │                │ │
│ │ ┌────────────┐ │ │                   │ │ ┌────────────┐ │ │    │ │ ┌────────────┐ │ │
│ │ │ LRU Evict │ │ │                   │ │ │ LRU Evict │ │ │    │ │ │ LRU Evict │ │ │
│ │ └────────────┘ │ │                   │ │ └────────────┘ │ │    │ │ └────────────┘ │ │
│ │ ┌────────────┐ │ │                   │ │ ┌────────────┐ │ │    │ │ ┌────────────┐ │ │
│ │ │ Expire Mgr │ │ │                   │ │ │ Expire Mgr │ │ │    │ │ │ Expire Mgr │ │ │
│ │ └────────────┘ │ │                   │ │ └────────────┘ │ │    │ │ └────────────┘ │ │
│ └────────────────┘ │                   │ └────────────────┘ │    │ └────────────────┘ │
│ ┌────────────────┐ │                   │ ┌────────────────┐ │    │ ┌────────────────┐ │
│ │ Persistence     │ │                   │ │ Persistence     │ │    │ │ Persistence     │ │
│ │ - RDB Snapshot │ │                   │ │ - RDB Snapshot │ │    │ │ - RDB Snapshot │ │
│ │ - AOF Log      │ │                   │ │ - AOF Log      │ │    │ │ - AOF Log      │ │
│ └────────────────┘ │                   │ └────────────────┘ │    │ └────────────────┘ │
└────────────────────┘                   └────────────────────┘    └────────────────────┘
```

---

## 核心深入

### 数据分片：一致性哈希 vs 虚拟节点

#### 方案一：简单哈希取模

```
分片: node_index = hash(key) % N

问题:
  - 增加节点: 几乎所有 key 都需要重新映射
  - 删除节点: 同上
  - 数据迁移量: ~100%
  - 灾难性的重哈希操作
  
❌ 不适用于动态扩缩容
```

#### 方案二：一致性哈希 (Consistent Hashing)

```
原理:
  将哈希空间组织成一个环 (0 ~ 2^32-1)
  节点和数据都映射到环上的位置
  数据存储在顺时针方向第一个节点上

  增加节点: 只影响 ~1/N 的数据迁移
  删除节点: 只影响 ~1/N 的数据重新分配
  
优点: 数据迁移量最小化
缺点: 负载不均 (节点哈希位置随机)
```

#### 方案三：一致性哈希 + 虚拟节点 (Virtual Nodes)【推荐】

```
原理:
  每个物理节点映射到环上的 M 个虚拟节点 (通常 100-200 个)
  虚拟节点均匀分布在环上
  
  例如:
    Physical Node A → VNode A1, A2, ..., A150
    Physical Node B → VNode B1, B2, ..., B150
  
优点:
  - 负载均衡: 虚拟节点越多，分布越均匀
  - 扩缩容平滑: 虚拟节点逐个迁移
  - 支持异构节点: 高性能节点可分配更多虚拟节点

参数选择:
  - M = 100~200：在均衡性和元数据开销间的最优平衡
  - Dynamo 使用 virtual nodes
  - Cassandra 使用 virtual nodes (num_tokens)
```

```python
import hashlib
import bisect

class ConsistentHash:
    def __init__(self, virtual_nodes_per_physical=150):
        self.vnodes_per_physical = virtual_nodes_per_physical
        self.ring = {}      # hash_value → physical_node
        self.sorted_keys = []  # 排序的哈希值列表
        self.nodes = set()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16) & 0xFFFFFFFF

    def add_node(self, node_id: str):
        self.nodes.add(node_id)
        for i in range(self.vnodes_per_physical):
            vnode_key = f"{node_id}:vnode:{i}"
            hash_val = self._hash(vnode_key)
            self.ring[hash_val] = node_id
            bisect.insort(self.sorted_keys, hash_val)

    def remove_node(self, node_id: str):
        self.nodes.discard(node_id)
        for i in range(self.vnodes_per_physical):
            vnode_key = f"{node_id}:vnode:{i}"
            hash_val = self._hash(vnode_key)
            if hash_val in self.ring:
                del self.ring[hash_val]
                self.sorted_keys.remove(hash_val)

    def get_node(self, key: str) -> str:
        if not self.ring:
            raise Exception("No nodes in ring")
        hash_val = self._hash(key)
        # Binary search to find first node >= hash_val
        idx = bisect.bisect_right(self.sorted_keys, hash_val)
        if idx == len(self.sorted_keys):
            idx = 0  # wrap around the ring
        return self.ring[self.sorted_keys[idx]]

    def get_replica_nodes(self, key: str, replica_count: int) -> list:
        """获取前 N 个复制节点（顺时针）"""
        nodes = []
        hash_val = self._hash(key)
        idx = bisect.bisect_right(self.sorted_keys, hash_val)
        for i in range(len(self.sorted_keys)):
            node_hash = self.sorted_keys[(idx + i) % len(self.sorted_keys)]
            node = self.ring[node_hash]
            if node not in nodes:
                nodes.append(node)
            if len(nodes) == replica_count:
                break
        return nodes
```

### 复制策略

```
复制策略对比:

┌─────────────────────────────────────────────────────────────────┐
│                    主从复制 vs 多主复制                             │
│                                                                 │
│  主从复制 (Primary-Replica / Leader-Follower):                     │
│    ┌──────────┐                                                  │
│    │  Master  │──── Write ────▶ ┌──────────┐  ┌──────────┐     │
│    │  (RW)   │                 │ Slave-1  │  │ Slave-2  │     │
│    └──────────┘                 │  (RO)    │  │  (RO)    │     │
│                                 └──────────┘  └──────────┘     │
│    优点: 简单、强一致（主）、无写冲突                              │
│    缺点: 主单点（需故障转移）、写入不水平扩展                        │
│    代表: Redis (标准模式)                                        │
│                                                                 │
│  多主复制 (Multi-Master / Leaderless):                            │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐                │
│    │  Node A  │◀──▶│  Node B  │◀──▶│  Node C  │                │
│    │  (RW)    │    │  (RW)    │    │  (RW)    │                │
│    └──────────┘    └──────────┘    └──────────┘                │
│    优点: 高可用、无单点、写入水平扩展                              │
│    缺点: 写冲突、一致性难保证、实现复杂                             │
│    代表: DynamoDB, Cassandra, Riak                              │
│                                                                 │
│  推荐: 组合使用                                                    │
│    - 缓存型 KV (Redis类): 主从复制                                │
│    - 持久化 KV (DynamoDB类): 多主复制 + 一致性协议                  │
└─────────────────────────────────────────────────────────────────┘
```

### 一致性模型

```
┌─────────────────────────────────────────────────────────────────┐
│                    一致性模型频谱                                  │
│                                                                 │
│  Strong           Sequential         Causal           Eventual  │
│  (强一致)          (顺序一致)          (因果一致)        (最终一致)  │
│  ────────────────────────────────────────────────────────────── │
│  │                │                  │                  │       │
│  │ R + W > N      │ Vector Clock     │ Lamport/         │       │
│  │ (Quorum)       │ + R=W=QUORUM    │ Version Clock    │       │
│  │                │                  │                  │       │
│  最严格            │                  │                  最宽松   │
│                                                                 │
│  Quorum 读写 (Dynamo 风格):                                      │
│                                                                 │
│  设 N = 副本总数                                                  │
│     R = 读操作需要接收到响应的副本数                                │
│     W = 写操作需要接收到响应的副本数                                │
│                                                                 │
│  强一致: R + W > N                                               │
│    例如: N=3, R=2, W=2 → 任意读一定包含最新写                      │
│    例如: N=3, R=3, W=1 → 高可用写, 读强一致但低可用                │
│                                                                 │
│  最终一致: R = 1, W = 1                                           │
│    写入主后异步同步到副本                                          │
│    读可能缺失最新数据                                              │
│    需要冲突解决机制                                                │
│                                                                 │
│  Quorum 组合推荐:                                                 │
│    强一致性场景: N=3, R=2, W=2 (R+W=4 > N=3)                      │
│    读优化场景:  N=3, R=1, W=3 (R+W=4 > N=3, 写慢但读快)          │
│    写优化场景:  N=3, R=3, W=1 (R+W=4 > N=3, 读慢但写快)          │
│    高可用场景:  N=3, R=2, W=2 (均衡)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 冲突解决：版本向量 vs 最后写入胜出

```
版本向量 (Version Vector / Vector Clock):

每个节点维护一个 {node_id: counter} 映射
  例: 初始 [A:0, B:0, C:0]
  
  Client 写入 Node A → [A:1, B:0, C:0]
  Client 写入 Node B → [A:0, B:1, C:0]
  并行冲突! 需要应用层解决

  Client 读取 → 收到两个版本:
    v1: [A:1, B:0, C:0]  value="张三"
    v2: [A:0, B:1, C:0]  value="李四"
  Client 解决冲突后写入 → [A:1, B:1, C:0] value="张三" (选择v1)

LWW (Last-Write-Wins):
  基于时间戳，最新时间戳的写入"胜出"
  优点: 简单自动
  缺点: 可能丢失数据 (时钟回拨、同一时间多写)
  适用: 缓存场景、幂等性强的数据
```

```python
class VectorClock:
    def __init__(self):
        self.clock = {}  # {node_id: counter}

    def increment(self, node_id: str):
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock'):
        for node_id, count in other.clock.items():
            self.clock[node_id] = max(self.clock.get(node_id, 0), count)

    def compare(self, other: 'VectorClock') -> str:
        """比较两个版本向量: before | after | concurrent"""
        all_greater_equal = True   # self >= other for all keys
        all_less_equal = True      # self <= other for all keys
        all_keys = set(self.clock.keys()) | set(other.clock.keys())

        for k in all_keys:
            s = self.clock.get(k, 0)
            o = other.clock.get(k, 0)
            if s > o: all_less_equal = False
            if s < o: all_greater_equal = False

        if all_greater_equal and all_less_equal:
            return 'equal'
        if all_greater_equal:
            return 'after'     # self 是 newer
        if all_less_equal:
            return 'before'    # self 是 older
        return 'concurrent'    # 冲突!
```

### 过期键删除策略

```
Redis 使用的三种过期删除策略:

1. 惰性删除 (Lazy Expiration):
   - 访问 key 时检查是否过期
   - 过期则删除并返回不存在
   - 优点: CPU 友好
   - 缺点: 内存泄漏 (冷数据永远占用内存)

2. 定期删除 (Periodic / Active Expiration):
   - 后台定时任务 (每 100ms) 随机扫描 20 个带 TTL 的 key
   - 如果过期比例 > 25%，重复扫描
   - 限制每次执行时间 < 25% CPU
   - 优点: 平衡 CPU 和内存

3. 惰性 + 定期删除 (Redis 默认) 【推荐】:
   - GET 时惰性检查 + 后台定期扫描
   - 配合 LRU/LFU 内存淘汰 (内存满时)

LRU vs LFU 淘汰策略:

LRU (Least Recently Used):
  - 使用链表 (最近使用在头, 最少使用在尾)
  - 内存满时淘汰尾节点
  - 问题: 周期性批量访问的冷数据可能被误保留

LFU (Least Frequently Used):
  - 记录每个 key 的访问频率
  - 内存满时淘汰频率最低的
  - 优点: 保留真实热点
  - 实现: Morris Counter (概率计数, 内存友好)
```

---

## 扩展性与高可用

### 故障检测与恢复

```
Gossip 协议成员发现:

每隔 1 秒, 每个节点:
  1. 随机选择 3 个其他节点
  2. 向它们发送 PING (包含自身元数据 + 已知拓扑)
  3. 接收 PONG 响应 (包含对方元数据 + 最新拓扑)
  4. 更新本地拓扑视图

故障检测:
  - φ Accrual Failure Detection (Cassandra 使用)
  - 基于心跳间隔的统计模型计算可疑度 (φ)
  - φ > 阈值 (default 8) → 标记为疑似故障 (SUSPECT)
  - 在区间内确认或超时 → 标记为 DOWN

故障恢复:

节点 A 被检测为 DOWN:
  1. Gossip 协议广播 A 的状态
  2. A 负责的 token range 需要由邻居接管
  3. Hinted Handoff (提示移交):
     - 写入请求改为写入邻居节点 (临时接管)
     - 邻居节点在额外存储中保留 "Hint" 标记 (目标节点 = A)
     - A 恢复后, 邻居把 Hint 数据推送回去
  4. Read Repair:
     - 读请求时检测各副本版本差异
     - 自动修复落后的副本
```

### Hinted Handoff 机制

```
Hinted Handoff 流程:

正常时:
  Key "foo" → hash → Token 50 → 主副本: Node A, 备副本: B, C

A 宕机时:
  Coordinator (客户端或代理) 收到写入请求
  → 目标 Node A 不可达
  → 将数据临时写入一致性哈希环上的下一个节点 (Node D)
  → 数据打上 Hint: {target_node: A, original_coordinator: X, timestamp: T}
  → 返回成功给客户端 (W=2 写入 B 和 D, 满足 Quorum)

A 恢复后:
  → A 检测到自身离开期间可能有 Hint
  → A 通知所有节点: "I'm back, send me hints"
  → D 将 Hint 数据回传给 A
  → A 确认接收后 D 删除 Hint 数据
  → Hint 清理完毕

Hint 数据的生命周期:
  - 默认保留 3 小时 (可配置)
  - 超时后自动丢弃 (避免无限堆积)
  - 丢弃意味着该写入可能丢失 (反熵修复可补救)
```

### 反熵修复 (Anti-Entropy / Merkle Tree)

```
Merkle Tree 用于副本间数据差异检测:

构造:
  1. 将 key 按 token range 分成多个区间
  2. 每个区间构建 Merkle Tree
  3. 叶子节点: hash(keys + values) of the range
  4. 内部节点: hash(children_hashes)
  5. 根节点: 整个区间内容的完整性哈希

差异检测:
  Node A 和 Node B 比较同一个 token range:
  1. 交换 Merkle Tree 根哈希
  2. 如果根哈希相同 → 数据一致，不用继续
  3. 如果根哈希不同 → 递归比较子节点哈希
  4. 定位到具体的叶子（最小差异区间）
  5. 交换并修复该区间的数据

优点:
  - O(log n) 比较复杂度
  - 网络传输量小 (仅交换哈希)
  - 精确定位差异区间
  
Cassandra 使用 Merkle Tree 进行反熵修复
```

---

## 总结

分布式键值存储是分布式系统的基石，核心设计维度：

1. **CAP 权衡**：根据场景选择 CP（强一致，如 etcd）或 AP（高可用，如 DynamoDB/Cassandra）或组合
2. **数据分片**：一致性哈希 + 虚拟节点是动态扩缩容的标准方案
3. **复制策略**：主从（简单）vs 多主（高可用），Quorum (R+W > N) 实现可调一致性
4. **冲突解决**：LWW（简单但有风险）vs Vector Clock（精确但复杂）
5. **故障恢复**：Gossip 协议 + Hinted Handoff + Read Repair + Anti-Entropy 四层防线
6. **持久化**：RDB 快照 + AOF 日志提供了不同级别的一致性和性能权衡
7. **过期清理**：惰性 + 定期删除 + LRU/LFU 淘汰的三重机制
8. **内存管理**：高效哈希表 + 渐进式 Rehash + 紧凑数据结构（ziplist/skiplist）

**面试核心权衡讨论：**
- CP vs AP：何时选择强一致，何时选择高可用
- 一致性实现：Quorum (R+W>N) vs Paxos/Raft
- 冲突解决：LWW vs Vector Clock + 应用层融合
- 持久化：RDB vs AOF vs 混合
- 过期策略：惰性 vs 定期 vs 混合
- 哈希表实现：链式哈希 vs 开放寻址 vs 跳表
- 多线程 vs 单线程：简单的线程模型 vs IO 多路复用
