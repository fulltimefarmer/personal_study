# 50. 设计布隆过滤器的分布式实现 (Design Distributed Bloom Filter Implementation)

## 题目

设计一个分布式布隆过滤器(Bloom Filter)，用于大规模去重场景（如URL去重、分布式缓存穿透防护、用户行为去重）。核心挑战是将布隆过滤器从单机扩展到分布式环境，支持海量数据(百亿级)和低误报率，同时保持高效的添加和查询性能。

## 需求澄清

### 功能性需求

1. **元素添加 (Add)**: 将元素(key)添加到布隆过滤器
2. **存在性查询 (Might Contain)**: 查询元素是否"可能存在"于集合中
3. **批量操作 (Batch Add/Query)**: 批量添加和查询，减少网络往返
4. **可配置误报率**: 创建时指定期望容量(n)和目标误报率(p)
5. **持久化 (Persistence)**: 布隆过滤器位图可持久化到磁盘，重启不丢失
6. **删除支持 (Delete)**: 可选，使用计数布隆过滤器(Counting Bloom Filter)
7. **动态扩容 (Scaling)**: 当容量接近上限时，自动扩展(可扩展布隆过滤器)

### 非功能性需求

1. **高吞吐**: 单节点 > 100K QPS 添加， > 500K QPS 查询
2. **低延迟**: P99 < 1ms (内存操作)
3. **分布式**: 支持横向扩展至多节点，应对百亿级元素
4. **低内存占用**: 100亿元素，误报率 0.1% → ~14GB (布隆过滤器)
5. **高可用**: 节点宕机不影响整体功能，提供副本/备份
6. **一致性**: 不同节点间的布隆过滤器状态一致（节点间同步）

### 容量估算

```
布隆过滤器内存计算:
  公式: m = -n × ln(p) / (ln(2))²
  其中: n = 元素数量, p = 误报率

  场景1: 100亿URL去重, p=0.1%
    m = -10¹⁰ × ln(0.001) / (ln(2))² 
      ≈ 10¹⁰ × 6.908 / 0.4805
      ≈ 1.438 × 10¹¹ bits
      ≈ 17.2 GB

  场景2: 100亿URL去重, p=1%
    m ≈ 9.6 GB

  场景3: 1亿用户行为去重, p=0.01%
    m ≈ 234 MB

QPS 估算:
  全网URL爬虫去重:
    日均URL: 100亿
    峰值添加 QPS: 100亿 / 86400 × 3(峰值系数) ≈ 350K QPS
    查询 QPS: 添加的10倍(每个新URL先查后加) ≈ 3.5M QPS

  分布式缓存穿透防护:
    缓存Key预估: 100亿个
    查询 QPS: 10M QPS (缓存层承载的流量)
    添加 QPS: 100K QPS (新Key写入)
```

## API设计

```protobuf
service DistributedBloomFilter {
  // 创建布隆过滤器
  rpc Create(CreateRequest) returns (CreateResponse);

  // 添加元素
  rpc Add(AddRequest) returns (AddResponse);
  rpc BatchAdd(BatchAddRequest) returns (BatchAddResponse);

  // 查询元素
  rpc MightContain(MightContainRequest) returns (MightContainResponse);
  rpc BatchMightContain(BatchMightContainRequest) returns (BatchMightContainResponse);

  // 管理操作
  rpc GetStats(GetStatsRequest) returns (GetStatsResponse);
  rpc Persist(PersistRequest) returns (PersistResponse);
  rpc Load(LoadRequest) returns (LoadResponse);
  rpc Delete(DeleteRequest) returns (DeleteResponse);
}

message CreateRequest {
  string filter_name = 1;            // 布隆过滤器名称
  int64 expected_elements = 2;       // 期望元素数量
  double error_rate = 3;             // 目标误报率 (如 0.001 = 0.1%)
  int32 shard_count = 4;             // 分片数量 (默认=1)
  FilterType type = 5;              // STANDARD / COUNTING / SCALABLE
  int32 replication_factor = 6;     // 副本因子 (默认=1)
  int32 ttl_seconds = 7;            // 过期时间, 0=永不过期
}

message AddRequest {
  string filter_name = 1;
  bytes element = 2;                 // 被添加的元素
}

message MightContainResponse {
  string filter_name = 1;
  bytes element = 2;
  bool present = 3;                  // true = 可能存在, false = 绝对不存在
}

message BatchMightContainRequest {
  string filter_name = 1;
  repeated bytes elements = 2;
}

message BatchMightContainResponse {
  repeated ItemResult results = 1;

  message ItemResult {
    bytes element = 1;
    bool present = 2;
  }
}

message GetStatsResponse {
  string filter_name = 1;
  int64 total_bits = 2;
  int64 set_bits = 3;                // 已设置的位数
  double fill_ratio = 4;             // 填充率 = set_bits / total_bits
  int64 estimated_elements = 5;      // 估算的已添加元素数
  double current_error_rate = 6;     // 当前实际误报率
}
```

## 数据模型

### 单节点布隆过滤器

```
布隆过滤器位图结构:
┌────────────────────────────────────────────────────┐
│              Bit Array (m bits)                     │
│  ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐  │
│  │ 1│ 0│ 0│ 1│ 0│ 0│ 1│ 0│ 1│ 0│ 0│ 0│ 1│ 0│ 0│  │
│  └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘  │
│  Bit 0              Bit 7              Bit 14      │
└────────────────────────────────────────────────────┘

添加元素 "item1":
  hash1("item1") % m = 2   → 设置 bit2  = 1
  hash2("item1") % m = 7   → 设置 bit7  = 1
  hash3("item1") % m = 12  → 设置 bit12 = 1

查询元素 "item2":
  hash1("item2") % m = 2   → bit2  = 1 ✓
  hash2("item2") % m = 5   → bit5  = 0 ✗ → 绝对不存在!

哈希函数数量(k):
  k = (m/n) × ln(2) = -ln(p) / ln(2)
  当 p = 0.001: k ≈ 10
```

### 分片布隆过滤器 (Sharded Bloom Filter)

```
将布隆过滤器拆分为多个独立分片:

┌────────────────────────────────────────────────────┐
│               Distributed Bloom Filter              │
│                                                     │
│  element → hash(element) % 分片数 = shard_id        │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Shard 0  │  │ Shard 1  │  │ Shard 2          │  │
│  │ n/N elem │  │ n/N elem │  │ n/N elem         │  │
│  │ 1.7 GB   │  │ 1.7 GB   │  │ 1.7 GB          │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│  Redis Cluster / 独立Redis节点                      │
│  每个分片独立运行, 可分布在不同机器上                  │
└────────────────────────────────────────────────────┘
```

### Redis 数据结构 (使用 RedisBloom 模块)

```
# 标准布隆过滤器
BF.RESERVE url_filter 0.001 10000000000
#               name     p=0.1%  n=100亿

BF.ADD url_filter "https://example.com/page1"
BF.EXISTS url_filter "https://example.com/page1"  → 1
BF.EXISTS url_filter "https://example.com/page2"  → 0

BF.MADD url_filter "url1" "url2" "url3"
BF.MEXISTS url_filter "url1" "url2" "url3"

# 计数布隆过滤器 (支持删除)
BF.RESERVE counting_filter 0.01 1000000

# 查看信息
BF.INFO url_filter
# 返回: Capacity, Size, Number of filters, Number of items inserted,
#       Expansion rate

# 布谷鸟过滤器 (Cuckoo Filter) - 支持删除+更低内存
CF.RESERVE cuckoo_filter 10000000
CF.ADD cuckoo_filter "item1"
CF.DEL cuckoo_filter "item1"     # 支持删除!
CF.EXISTS cuckoo_filter "item1"

# 布隆过滤器持久化
BF.SCANDUMP url_filter 0          # 开始扫描dump
BF.LOADCHUNK url_filter 0 <data>  # 加载dump数据
```

### 持久化存储方案

```sql
-- 布隆过滤器元数据表
CREATE TABLE bloom_filters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    filter_name VARCHAR(128) NOT NULL UNIQUE,
    expected_elements BIGINT NOT NULL,
    error_rate DOUBLE NOT NULL,
    total_bits BIGINT NOT NULL,
    hash_count INT NOT NULL,
    shard_count INT NOT NULL DEFAULT 1,
    filter_type ENUM('STANDARD','COUNTING','SCALABLE','CUCKOO') NOT NULL,
    status ENUM('ACTIVE','PAUSED','DELETED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 布隆过滤器持久化块 (用于灾难恢复)
CREATE TABLE bloom_filter_chunks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    filter_name VARCHAR(128) NOT NULL,
    chunk_index INT NOT NULL,
    chunk_data LONGBLOB NOT NULL,                -- 压缩后的位图数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_filter_chunk (filter_name, chunk_index)
) ENGINE=InnoDB;
```

## 高层次架构

```
                       ┌─────────────────────────────────┐
                       │          Client / SDK            │
                       │  BloomFilterClient              │
                       │  - 本地哈希计算                  │
                       │  - 分片路由 (hash%N)            │
                       │  - 本地布隆过滤器缓存(可选)       │
                       │  - 批处理聚合                    │
                       └───────────────┬─────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
            ┌───────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
            │ BF Shard 0   │   │ BF Shard 1  │   │ BF Shard N  │
            │ (Redis)      │   │ (Redis)     │   │ (Redis)     │
            │              │   │             │   │             │
            │ ┌──────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │
            │ │Bloom     │ │   │ │Bloom    │ │   │ │Bloom    │ │
            │ │Filter    │ │   │ │Filter   │ │   │ │Filter   │ │
            │ │Bitmap    │ │   │ │Bitmap   │ │   │ │Bitmap   │ │
            │ └──────────┘ │   │ └─────────┘ │   │ └─────────┘ │
            │              │   │             │   │             │
            │ ┌──────────┐ │   │ ┌─────────┐ │   │ ┌─────────┐ │
            │ │Replica   │ │   │ │Replica  │ │   │ │Replica  │ │
            │ │(Standby) │ │   │ │(Standby)│ │   │ │(Standby)│ │
            │ └──────────┘ │   │ └─────────┘ │   │ └─────────┘ │
            └───────┬──────┘   └──────┬──────┘   └──────┬──────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │  Bitmap Sync Service │
                            │  - AOF / RDB 持久化   │
                            │  - 定期全量备份到S3   │
                            │  - 跨DC异步复制      │
                            └──────────┬──────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   S3 / HDFS / NAS   │
                            │   (冷备份存储)       │
                            └─────────────────────┘
```

### 数据流

```
写入流程:
  1. Client 调用: bf.add("item_abc")
  2. SDK 计算分片: shard = hash("item_abc") % N
  3. SDK 将请求路由到对应分片的 Redis
  4. Redis 执行 BF.ADD filter_name "item_abc"
  5. 异步持久化: AOF 追加记录 / 定期 RDB 快照

查询流程:
  1. Client 调用: bf.mightContain("item_abc")
  2. SDK 计算分片: shard = hash("item_abc") % N
  3. SDK 将查询发送到对应分片
  4. Redis 执行 BF.EXISTS filter_name "item_abc"
  5. 返回: true(可能存在) / false(绝对不存在)

批量流程:
  1. Client 发送 100 个元素
  2. SDK 按分片分组:
     shard_0: ["item_1","item_5",...]
     shard_1: ["item_2","item_3",...]
  3. SDK 并行发送到各分片 (Pipeline)
  4. 各分片独立处理, 聚合结果返回
```

## 核心深入

### 布隆过滤器算法详解

```python
import hashlib
import math
import struct
import mmap
import os

class BloomFilter:
    """单节点布隆过滤器实现"""

    def __init__(self, expected_elements: int, error_rate: float):
        self.n = expected_elements
        self.p = error_rate

        # 计算最优位数组大小 m
        self.m = self._optimal_m(expected_elements, error_rate)

        # 计算最优哈希函数数量 k
        self.k = self._optimal_k(self.m, expected_elements)

        # 分配位数组 (使用 bytearray 或 mmap)
        byte_size = (self.m + 7) // 8
        self.bit_array = bytearray(byte_size)

        # 统计
        self.element_count = 0

    def _optimal_m(self, n: int, p: float) -> int:
        """最优位数组大小: m = -n*ln(p) / (ln(2))²"""
        return int(-n * math.log(p) / (math.log(2) ** 2))

    def _optimal_k(self, m: int, n: int) -> int:
        """最优哈希函数数量: k = (m/n)*ln(2)"""
        return max(1, int((m / n) * math.log(2)))

    def _get_hashes(self, element: bytes) -> list:
        """
        使用双重哈希技巧生成 k 个哈希值
        h(i, x) = hash1(x) + i * hash2(x), i = 0,1,...,k-1

        只需要计算两个独立哈希, 组合出 k 个哈希值
        类似于 Kirsch-Mitzenmacher 优化
        """
        h1 = struct.unpack('>Q', hashlib.sha256(b'1' + element).digest()[:8])[0]
        h2 = struct.unpack('>Q', hashlib.sha256(b'2' + element).digest()[:8])[0]

        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, element: str):
        """添加元素"""
        element_bytes = element.encode('utf-8')
        for position in self._get_hashes(element_bytes):
            byte_idx = position // 8
            bit_idx = position % 8
            self.bit_array[byte_idx] |= (1 << bit_idx)
        self.element_count += 1

    def might_contain(self, element: str) -> bool:
        """查询元素"""
        element_bytes = element.encode('utf-8')
        for position in self._get_hashes(element_bytes):
            byte_idx = position // 8
            bit_idx = position % 8
            if not (self.bit_array[byte_idx] & (1 << bit_idx)):
                return False  # 任何一个位为0 → 绝对不存在
        return True  # 所有位都为1 → 可能存在(有误报可能)

    def estimated_fill_ratio(self) -> float:
        """估算填充率"""
        set_bits = sum(bin(byte).count('1') for byte in self.bit_array)
        return set_bits / self.m

    def current_error_rate(self) -> float:
        """当前实际误报率"""
        # 近似: p ≈ (填充率)^k
        fill_ratio = self.estimated_fill_ratio()
        return fill_ratio ** self.k

    def save_to_file(self, filepath: str):
        """持久化到文件"""
        with open(filepath, 'wb') as f:
            # 写入元数据头
            f.write(struct.pack('>QQQ', self.n, self.m, self.k))
            f.write(bytes(self.bit_array))

    @classmethod
    def load_from_file(cls, filepath: str):
        """从文件加载"""
        with open(filepath, 'rb') as f:
            n, m, k = struct.unpack('>QQQ', f.read(24))
            bf = cls.__new__(cls)
            bf.n = n
            bf.m = m
            bf.k = k
            byte_size = (m + 7) // 8
            bf.bit_array = bytearray(f.read(byte_size))
            return bf
```

### 分布式分片策略

```python
class DistributedBloomFilter:
    """分片布隆过滤器客户端"""

    def __init__(self, redis_cluster, shard_count=10):
        self.redis_cluster = redis_cluster
        self.shard_count = shard_count
        # 分片到Redis节点的映射
        self.shard_to_redis = self._build_shard_mapping()

    def _get_shard(self, element: str) -> int:
        """确定元素属于哪个分片"""
        element_hash = hashlib.md5(element.encode()).digest()
        shard = struct.unpack('>I', element_hash[:4])[0] % self.shard_count
        return shard

    def add(self, filter_name: str, element: str):
        """添加元素: 只写一个分片"""
        shard = self._get_shard(element)
        redis_node = self.shard_to_redis[shard]
        return redis_node.execute_command(
            'BF.ADD', f'{filter_name}:shard:{shard}', element
        )

    def might_contain(self, filter_name: str, element: str) -> bool:
        """查询元素: 只查一个分片"""
        shard = self._get_shard(element)
        redis_node = self.shard_to_redis[shard]
        return redis_node.execute_command(
            'BF.EXISTS', f'{filter_name}:shard:{shard}', element
        )

    def batch_might_contain(self, filter_name: str, elements: list):
        """批量查询: 按分片分组后并行查询"""
        # 按分片分组
        shard_groups = {}
        for i, element in enumerate(elements):
            shard = self._get_shard(element)
            if shard not in shard_groups:
                shard_groups[shard] = []
            shard_groups[shard].append((i, element))

        # 每组分片独立Pipeline查询
        results = [None] * len(elements)
        for shard, items in shard_groups.items():
            redis_node = self.shard_to_redis[shard]
            pipe = redis_node.pipeline()
            for idx, element in items:
                pipe.execute_command(
                    'BF.EXISTS', f'{filter_name}:shard:{shard}', element
                )
            pipe_results = pipe.execute()
            for (idx, _), result in zip(items, pipe_results):
                results[idx] = bool(result)

        return results
```

### 可扩展布隆过滤器 (Scalable Bloom Filter)

```
问题: 初始容量不足时怎么办?
  标准布隆过滤器满了后, 误报率急剧上升

解决方案: 可扩展布隆过滤器
  当前过滤器填满后, 追加一个新的过滤器
  查询时检查所有过滤器

┌─────────┐   ┌─────────┐   ┌─────────┐
│Filter 1 │   │Filter 2 │   │Filter 3 │
│ n=100万  │   │ n=200万  │   │ n=400万  │  ← 每个容量翻倍
│ p=0.001  │   │ p=0.0005 │   │ p=0.00025│  ← 误报率收紧
│ m=14.4Mb │   │ m=19.2Mb │   │ m=24Mb   │
└─────────┘   └─────────┘   └─────────┘

总体误报率:
  P_total = 1 - ∏(1 - p_i) 
          ≈ 0.001 + 0.0005 + 0.00025 ≈ 0.00175
```

```python
class ScalableBloomFilter:
    """可扩展布隆过滤器"""

    def __init__(self, initial_capacity=1_000_000, error_rate=0.001,
                 growth_factor=2, tightning_ratio=0.5):
        self.filters = []
        self.initial_capacity = initial_capacity
        self.initial_error_rate = error_rate
        self.growth_factor = growth_factor
        self.tightning_ratio = tightning_ratio

        # 创建第一个过滤器
        self._add_filter(initial_capacity, error_rate)

    def _add_filter(self, capacity, error_rate):
        bf = BloomFilter(capacity, error_rate)
        self.filters.append(bf)

    def add(self, element):
        """在最后一个(最新的)过滤器中添加"""
        self.filters[-1].add(element)

        # 检查是否需要扩容
        if self.filters[-1].estimated_fill_ratio() > 0.5:
            new_capacity = int(self.initial_capacity *
                               (self.growth_factor ** len(self.filters)))
            new_error = self.initial_error_rate * \
                        (self.tightning_ratio ** len(self.filters))
            self._add_filter(new_capacity, new_error)

    def might_contain(self, element):
        """在所有过滤器中查询"""
        for bf in self.filters:
            if bf.might_contain(element):
                return True
        return False
```

### 计数布隆过滤器 (Counting Bloom Filter)

```
问题: 标准布隆过滤器不支持删除

解决方案: 将每个位改成计数器(4-bit or 8-bit)
  Add:  hash1→counter_i += 1
  Delete: hash1→counter_i -= 1
  Query: hash1→counter_i > 0 ?

4-bit计数器: 最大计数15, 溢出处理 = 保持15不动

内存开销: 
  标准布隆过滤器: m bits
  计数布隆过滤器(4-bit): 4×m bits
  内存增加 4 倍
```

### 布隆过滤器 vs 布谷鸟过滤器 vs 其他

| 数据结构 | 删除支持 | 内存效率 | 查询性能 | 适用场景 |
|---------|---------|---------|---------|---------|
| Bloom Filter | ✗ | 优 (1x) | O(k) | 纯去重 |
| Counting Bloom Filter | ✓ | 中 (4x) | O(k) | 需删除的去重 |
| Cuckoo Filter | ✓ | 优+ | O(1) | 需删除+高负载 |
| Quotient Filter | ✓ | 优+ | O(1) | 大规模, 需合并 |
| XOR Filter | ✗ | 最优 | O(1) | 静态集合 |

```
布谷鸟过滤器 (Cuckoo Filter) 优势:
  - 支持删除
  - 在高负载(>75%)时性能仍好于布隆过滤器
  - 内存效率略优于布隆过滤器(同样误报率)
  - 可以使用两个哈希表实现
  - Redis 的 CF (Cuckoo Filter) 模块可用

选型建议:
  只需要添加+查询 → 标准布隆过滤器
  需要删除 → 布谷鸟过滤器 (优于计数布隆)
  集合静态不变 → XOR Filter (尺寸最小)
```

## 扩展性与高可用

### 多级缓存布隆过滤器

```
                      ┌─────────────────────────┐
                      │        Client SDK         │
                      │                           │
                      │  L0: 本地内存布隆过滤器     │
                      │       容量: 10万           │
                      │       延迟: <1μs           │
                      │       定期从L1同步          │
                      └───────────┬───────────────┘
                                  │ miss
                      ┌───────────▼───────────────┐
                      │   L1: 近端Redis分片        │
                      │        容量: 10亿           │
                      │        延迟: <1ms           │
                      └───────────┬───────────────┘
                                  │ miss(p=极低)
                      ┌───────────▼───────────────┐
                      │   L2: 精确去重 (DB/KV)     │
                      │        容量: 无限           │
                      │        延迟: ~10ms          │
                      └───────────────────────────┘
```

### 跨数据中心复制

```
布隆过滤器跨DC同步方案:

方案A: Redis AOF 异步复制
  主DC写入 → AOF日志 → 异步传输到备DC → 备DC重放AOF

方案B: 定期全量同步
  每 1 小时: 主DC DUMP位图 → 压缩 → 传输到备DC → 备DC LOAD

方案C: 双写
  客户端同时向两个DC的Redis写入

推荐: 方案A (AOF复制) + 方案B (定期全量快照) 组合
  - AOF保证实时性 (RPO < 1s)
  - 全量快照保证可恢复性
```

### 监控告警

| 指标 | 计算方式 | 告警阈值 |
|------|---------|---------|
| 填充率 (Fill Ratio) | set_bits / total_bits | > 50% (可能需扩容) |
| 估算元素数 | -m/k × ln(1 - set_bits/m) | > 80% of capacity |
| 当前误报率 | (fill_ratio)^k | 超过目标值的 2x |
| 查询延迟 P99 | prometheus histogram | > 5ms |
| 分片间数据偏差 | max(set_bits) / min(set_bits) | > 1.3 (负载不均) |
| Redis 内存 | info memory | > 80% |
| 持久化成功 | AOF/RDB 状态 | 连续失败 > 3次 |

## 总结

1. **布隆过滤器原理**: m个bits + k个哈希函数, 误报率 p ≈ (1-e^(-kn/m))^k, 最优 k=(m/n)ln(2)
2. **分布式分片**: hash(element) % N 确定分片, 查询/添加只需访问一个分片, 天然支持水平扩展
3. **双哈希优化**: Kirsch-Mitzenmacher 优化, 用2个独立哈希模拟k个哈希值
4. **可扩展布隆过滤器**: 容量不够时追加新过滤器, 容量翻倍 + 误报率减半
5. **布谷鸟过滤器优势**: 支持删除 + 内存效率高 + 高负载性能好
6. **Client-side分片**: SDk内计算分片 + Pipeline批量, 减少网络往返
7. **持久化**: AOF实时 + 定期RDB快照 + S3冷备份, 多重保障
8. **多级过滤**: L0本地缓存(μs级) → L1 Redis(ms级) → L2 DB精确查(10ms级)
9. **假阳性处理**: 布隆过滤器只是一个快速过滤器, 假阳性需要下游精确去重兜底

面试中可能追问: Bloom Filter vs Cuckoo Filter 的详细对比? 如何估算布隆过滤器的假阳性率? 如何合并两个布隆过滤器(OR操作)? 如何做交集(AND)?
