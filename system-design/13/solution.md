# 设计分布式缓存 (Design Distributed Cache)

## 题目

设计一个分布式缓存系统，类似 Redis / Memcached。支持低延迟、高并发、数据持久化、可水平扩展的内存缓存服务。

---

## 需求澄清

### 功能性需求

| 功能 | 描述 |
|------|------|
| KV 存储 | 支持 String / Hash / List / Set / Sorted Set 等数据结构 |
| TTL 过期 | 支持设置 Key 的过期时间 |
| 数据持久化 | 支持 RDB 快照 + AOF 日志 |
| 缓存淘汰 | LRU / LFU / TTL 等淘汰策略 |
| 分布式支持 | 数据分片, 多节点组成集群 |
| 发布订阅 | 支持 Pub/Sub 消息模式 |
| 事务 | 支持 MULTI/EXEC 事务 (可选) |
| Lua脚本 | 支持 Lua 脚本原子执行 |

### 非功能性需求

| 需求 | 目标值 |
|------|--------|
| 延迟 | P99 < 1ms (内存操作) |
| 吞吐量 | 单节点 10万+ QPS |
| 可用性 | 99.99% (Sentinel/Cluster 主从切换) |
| 持久性 | 可配置: 每次写刷盘 / 每秒刷盘 / 不刷盘 |
| 一致性 | 最终一致性 (主从异步复制) 或 强一致 (同步复制) |
| 可扩展性 | 水平扩展, 在线增删节点 |

### 容量估算

```
假设:
  - DAU: 1亿
  - 每个用户会话需要缓存 10 个 KV
  - 每个 KV 平均 1KB (包括 Key + Value + 元数据)
  - 活跃用户 10% 同时在线

在线用户: 1亿 × 10% = 1000万
总缓存项: 1000万 × 10 = 1亿个 KV
总内存: 1亿 × 1KB = 100GB
考虑 1主2从副本: 100GB × 3 = 300GB
考虑内存碎片(1.5x): 100GB × 1.5 = 150GB/节点

QPS估算:
  - 每个用户每秒产生 5 次缓存操作 (读4+写1)
  - 总 QPS: 1000万 × 5 = 5000万 QPS
  - 标准配置: 32节点, 每节点 ~156万 QPS
  - 实际上读多写少, 读写分离后 Master 负载更低

网络带宽:
  - 5000万 QPS × 1KB = 50 GB/s (峰值)
  - 每个节点 ~1.6 Gbps 带宽需求
  - 需要万兆网卡 + 多节点分担
```

---

## API设计

### 核心命令

```
=== 字符串 (String) ===
SET key value [EX seconds] [NX|XX]
GET key
INCR key / DECR key
MSET key1 v1 key2 v2 ... (批量设置)
MGET key1 key2 ... (批量获取)
SETNX key value (不存在则设置)
GETSET key value (设置并返回旧值)
STRLEN key

=== 哈希 (Hash) ===
HSET key field value
HGET key field
HGETALL key
HDEL key field [field...]
HLEN key
HINCRBY key field increment

=== 列表 (List) ===
LPUSH key value [value...]
RPUSH key value [value...]
LPOP key / RPOP key
LRANGE key start stop
LLEN key
BLPOP key [key...] timeout (阻塞式弹出)

=== 集合 (Set) ===
SADD key member [member...]
SMEMBERS key
SISMEMBER key member
SREM key member
SUNION key1 key2 / SINTER key1 key2 / SDIFF key1 key2
SCARD key

=== 有序集合 (Sorted Set) ===
ZADD key score member [score member...]
ZRANGE key min max [WITHSCORES]
ZRANK key member (按score排序)
ZSCORE key member
ZREM key member

=== 通用 ===
DEL key [key...]
EXPIRE key seconds
TTL key
EXISTS key
KEYS pattern  / SCAN cursor [MATCH pattern] (遍历)
TYPE key
RENAME key newkey

=== 发布/订阅 ===
PUBLISH channel message
SUBSCRIBE channel [channel...]
PSUBSCRIBE pattern (模式订阅)

=== 事务 ===
MULTI
  SET k1 v1
  INCR counter
EXEC

=== Lua 脚本 ===
EVAL "return redis.call('GET', KEYS[1])" 1 mykey
EVALSHA <sha1> 1 mykey (脚本缓存)
```

### 集群相关命令

```
=== 集群管理 ===
CLUSTER INFO                     # 集群状态信息
CLUSTER NODES                    # 集群节点列表
CLUSTER SLOTS                    # 槽位分配信息
CLUSTER ADDSLOTS <slot> [slot...]  # 分配槽位
CLUSTER MEET ip port             # 加入集群
CLUSTER REPLICATE node-id        # 设置为某节点的从节点
CLUSTER FORGET node-id           # 移除节点
CLUSTER KEYSLOT key              # 计算 key 所在槽位
CLUSTER RESHARD                  # 重新分片(迁移槽位)
```

---

## 数据模型

### 核心数据结构 (内存中的存储)

```
Redis 内部数据结构:

+--------------------------------------------------+
|              Redis Server (单线程)                |
|                                                    |
|  +------------------+  +------------------+        |
|  |    Dict (HT)     |  |    Expires Dict   |        |
|  |  Key -> Value    |  |  Key -> ExpireTime|        |
|  |  +------+------+ |  |  +------+--------+|        |
|  |  | key1 | obj1 | |  |  | key1 |  TS1   ||        |
|  |  | key2 | obj2 | |  |  | key2 |  TS2   ||        |
|  |  | key3 | obj3 | |  |  +------+--------+|        |
|  |  +------+------+ |  +------------------+        |
|  +------------------+                               |
|                                                    |
|  对象类型:                                          |
|  +----------+  +----------+  +----------+          |
|  |  String  |  |   List   |  |   Set    |          |
|  |  SDS/RAW |  | QuickList|  | Dict/    |          |
|  |  INT     |  | (ziplist+ |  | IntSet   |          |
|  |  EMBSTR  |  |  linked) |  |          |          |
|  +----------+  +----------+  +----------+          |
|                                                    |
|  +----------+  +----------+                        |
|  |   Hash   |  | SortedSet|                        |
|  | Dict/    |  | Skiplist |                        |
|  | ZipList  |  | + Dict   |                        |
|  +----------+  +----------+                        |
+--------------------------------------------------+
```

### String 类型内部编码

```
String 三种内部编码:
  - INT: value 是整数, ptr 直接存值 (省内存)
  - EMBSTR: value <= 44字节, 一次分配内存 (obj + SDS)
  - RAW: value > 44字节, 两次分配 (obj + SDS分开)

SDS (Simple Dynamic String):
+-----+--------+--------+
| len | alloc  | buf[]  |
| (4) | (4)    | (var)  |
+-----+--------+--------+
  - len: 已用长度
  - alloc: 已分配长度 (不含头和null)
  - buf: 实际数据 (C字符串兼容)
  - O(1)获取长度, 预分配减少realloc, 二进制安全
```

### Hash 类型内部编码

```
Hash 两种内部编码:

1. ZipList (压缩列表) — 数据量小时使用:
   hash-max-ziplist-entries = 512
   hash-max-ziplist-value = 64

2. HashTable — 数据量大时自动转换:
   +-----+     +--------+     +--------+
   | ht0 | --> | bucket0| --> |  k1|v1 |
   +-----+     | bucket1|     |  k3|v3 |
   | ht1 |     | bucket2| --> |  k2|v2 |
   +-----+     |  ...   |     +--------+
   | rehashIdx|
   +----------+

渐进式 Rehash:
  - ht[0] 是当前表, ht[1] 是新表 (扩容/缩容用)
  - rehashidx: -1=未rehash, >=0=正在rehash第N个bucket
  - 每次增删改查操作时迁移1个bucket
  - 将一次性大O(N)分摊到每次O(1)
```

### Sorted Set 内部编码

```
Sorted Set (ZSet):

+---------------------------+
|          ZSet             |
|                           |
|  +-----------+            |
|  |  Dict     |            |
|  | member->  |            |
|  |   score   |            |   用于 O(1) 查找 score
|  +-----------+            |
|                           |
|  +-----------+            |
|  | SkipList  |            |
|  |           |            |   用于 O(logN) 范围查找/排名
|  +-----------+            |
+---------------------------+

跳表结构:
Level 3: [Head] =====================================> [Tail]
Level 2: [Head] =============> [B:25] =============> [Tail]
Level 1: [Head] =====> [A:10] > [B:25] > [C:50] > [Tail]
Level 0: [Head] > [A:10] > [B:25] > [C:50] > [Tail]

每个节点有随机层数 (最高32层)
查找: 从最高层开始向下查找 (O(logN) 平均)
插入: 随机生成层数 (概率: 50%为1层, 25%为2层, ...)
```

### 持久化数据模型

```
=== RDB (Redis Database Backup) ===
格式: 二进制快照
触发时机:
  - SAVE: 阻塞主线程保存
  - BGSAVE: fork()子进程后台保存
  - 配置: save 900 1 (900秒有1个key变化)

文件结构:
+--------+--------+--------+
| REDIS  | DB 0   | DB N   | EOF | Checksum
| Header | KeyVal | KeyVal |     |
+--------+--------+--------+

优点: 恢复速度快, 文件紧凑
缺点: 可能丢失最后一次快照后的数据
  RPO (Recovery Point Objective): 取决于快照频率

=== AOF (Append-Only File) ===
格式: 文本RESP协议命令序列
写入策略 (appendfsync):
  - always: 每条写命令fsync (最安全, 最慢)
  - everysec: 每秒fsync一次 (默认, 折中)
  - no: 交给OS决定 (最快, 最不安全)

AOF 重写 (BGREWRITEAOF):
  fork 子进程, 基于当前内存状态生成紧凑的命令序列
  (SET k1 v1; SET k2 v2 -> 只写最终的 SET)
  避免 AOF 文件无限增长

AOF 文件结构:
*3\r\n$3\r\nSET\r\n$2\r\nk1\r\n$5\r\nhello\r\n

=== RDB + AOF 混合持久化 (Redis 4.0+) ===
AOF 文件前半部分是 RDB 格式的快照, 后半部分是 AOF 增量日志
结合了两者优点: 恢复快 + 数据安全
```

### 集群元数据

```
Redis Cluster 16184 个哈希槽 (Slot):

+-----------------------------------------------------------+
|     CRC16(key) % 16384  -> 确定数据落在哪个Slot            |
+-----------------------------------------------------------+

槽分配 (例如 3 Master 各1 Slave):

Master 0  (Slots 0-5460)          Master 1  (Slots 5461-10922)      Master 2  (Slots 10923-16383)
+------------------------+        +-------------------------+        +-------------------------+
|    Slot 0    ... 5460  |        |    Slot 5461 ... 10922  |        |    Slot 10923 ... 16383 |
+------------------------+        +-------------------------+        +-------------------------+
         |                                    |                                   |
+--------v--------+                   +-------v-------+                   +-------v-------+
|   Slave 0-1     |                   |   Slave 1-1   |                   |   Slave 2-1   |
| (Slots 0-5460)  |                   |(Slots 5461-   |                   |(Slots 10923-  |
|  副本           |                   | 10922) 副本    |                   | 16383) 副本    |
+-----------------+                   +---------------+                   +---------------+

节点间 Gossip 协议通信:
  - 端口: 6379 (客户端) + 16379 (集群总线)
  - 定期随机选择节点交换信息
  - 传播: 节点状态, 槽位分配, 故障检测
```

---

## 高层次架构

### 单机架构

```
+-----------------------------------------------------------------+
|                        Redis Server                              |
|                                                                   |
|  +--------------------+     +--------------------+                 |
|  |   Network Layer    |     |   Event Loop       |                 |
|  |  (epoll/kqueue)    |     |  (单线程处理命令)   |                 |
|  +--------+-----------+     +--------+-----------+                 |
|           |                          |                             |
|  +--------v-----------+     +--------v-----------+                 |
|  |  Connection        |     |    Command Parser   |                 |
|  |  Management        |     |  (RESP协议解析)     |                 |
|  +--------------------+     +--------------------+                 |
|                                                                   |
|  +----------------------------------------------------------------+|
|  |                       Command Execution                        ||
|  |  +----------+  +----------+  +----------+  +----------+        ||
|  |  | String   |  | Hash     |  | List     |  | Set      |        ||
|  |  | Command  |  | Command  |  | Command  |  | Command  |        ||
|  |  +----------+  +----------+  +----------+  +----------+        ||
|  +----------------------------------------------------------------+|
|                                                                   |
|  +--------------------------+    +------------------------------+  |
|  |   Memory Management      |    |   Persistence                |  |
|  |  (jemalloc / 内存分配器)  |    |  (RDB + AOF + 混合持久化)    |  |
|  +--------------------------+    +------------------------------+  |
|                                                                   |
|  +--------------------------+    +------------------------------+  |
|  |   Replication            |    |   Eviction (缓存淘汰)         |  |
|  |  (主从复制 + PSYNC)      |    |  (LRU/LFU/TTL/Random)        |  |
|  +--------------------------+    +------------------------------+  |
|                                                                   |
+-----------------------------------------------------------------+
```

### 集群架构

```
                         +-------------------+
                         |    Client (SDK)  |
                         | (Smart Client/   |
                         |  Cluster-Aware)  |
                         +--+------------+--+
                            |            |
              +-------------+            +-------------+
              |                                        |
              v                                        v
+---------------------------+        +---------------------------+
|       Master 0            |        |       Master 1            |
|    Slot: 0-5460           |        |    Slot: 5461-10922        |
|  +---------------------+  |        |  +---------------------+  |
|  | 主从复制             |  |        |  | 主从复制             |  |
|  +----------+----------+  |        |  +----------+----------+  |
|             |             |        |             |             |
+---------------------------+        +---------------------------+
              |                                        |
              v                                        v
+---------------------------+        +---------------------------+
|       Slave 0-1           |        |       Slave 1-1           |
|    Slot: 0-5460 (只读)    |        |    Slot: 5461-10922 (只读) |
+---------------------------+        +---------------------------+

+---------------------------+
|       Sentinel 集群       |
|  +-----+ +-----+ +-----+ |
|  | S1  | | S2  | | S3  | |
|  +-----+ +-----+ +-----+ |
|                           |
|  监控 + 故障检测 + 切换    |
+---------------------------+

Client 路由:
  1. 连接任意节点, 执行 CLUSTER SLOTS 获取槽位映射
  2. 本地缓存槽位映射 (Slot -> Node 映射表)
  3. 计算 CRC16(key) % 16384 确定目标节点
  4. 直接发送命令到目标节点
  5. 如果收到 MOVED 重定向, 更新本地缓存
  6. 如果收到 ASK 重定向 (槽位迁移中), 单次重定向
```

### 读写分离与主从复制

```
+------------------+          +------------------+
|    Master         |          |    Slave          |
| (读写)            |          |  (只读, 可配读写)  |
|                   |          |                   |
| replication offset:  |       | replication offset:|
|    master_repl_offset|       |    slave_repl_offset|
|                   |          |                   |
| Replication       |          | Replication       |
| Buffer            |=========>| (接收+应用)       |
|                   | 异步复制  |                   |
+------------------+          +------------------+

=== PSYNC (部分同步) ===
全量同步 (Full Resync):
  Master: BGSAVE -> 发送RDB文件 -> 发送复制缓冲区命令
  Slave: 接收RDB加载 -> 执行累积命令

部分同步 (Partial Resync, PSYNC):
  依赖 Replication ID + Offset:
    Slave 重连后发送: PSYNC <repl_id> <offset>
    Master 检查:
      - repl_id 一致 且 offset 在复制缓冲区范围内 -> 增量同步
      - 否则 -> 全量同步

复制缓冲区 (repl-backlog):
  - 环形缓冲区, 默认1MB
  - 存储最近的写命令
  - 大小决定允许 Slave 断开多久后仍可部分同步
  - repl-backlog-size 建议 = (断开秒数 × 写QPS × 命令平均大小)
```

---

## 核心深入

### 1. 单线程 vs 多线程 vs 混合

```
=== Redis 为什么用单线程？ ===
1. 内存操作极快: CPU不是瓶颈, 网络/内存带宽才是
2. 避免上下文切换和锁竞争: 单线程无需加锁
3. 简单可靠: bug更少, 调试容易

=== Redis 6.0+ 多线程 I/O ===
单线程模型局限:
  - 大 Key 删除 (DEL bigHash) 会阻塞
  - 大量连接时网络 I/O 是瓶颈

多线程 I/O 架构:
+-----------------------------------------------------+
|  Main Thread (命令执行, 单线程)                       |
|  +-------------------------------------------------+ |
|  |     Command Processing (数据处理, 单线程)         | |
|  +-------------------------------------------------+ |
+-----------------------------------------------------+
         ^                   |
         | (解析后的命令)     | (执行结果)
         |                   v
+----------------+  +----------------+  +----------------+
| IO Thread 0    |  | IO Thread 1    |  | IO Thread N    |
| (读/解析+回写)  |  | (读/解析+回写)  |  | (读/解析+回写)  |
+----------------+  +----------------+  +----------------+
         ^                   ^                   ^
         |                   |                   |
    +----+----+         +----+----+         +----+----+
    | Clients |         | Clients |         | Clients |
    +---------+         +---------+         +---------+

关键: 命令执行仍然是单线程的, 多线程只用于网络 I/O
```

### 2. 缓存淘汰策略 (Eviction)

```
淘汰策略对比:

+---------------------------+----------------------------------------------+
| 策略                      | 描述                                          |
+---------------------------+----------------------------------------------+
| noeviction                | 不淘汰, 内存满时写入返回错误 (默认)            |
| allkeys-lru               | 所有 Key 参与 LRU 淘汰                        |
| volatile-lru              | 仅有过期时间 Key 参与 LRU 淘汰                |
| allkeys-random            | 所有 Key 随机淘汰                             |
| volatile-random           | 仅有过期时间 Key 随机淘汰                     |
| volatile-ttl              | 淘汰剩余 TTL 最短的 Key                        |
| allkeys-lfu (4.0+)        | 所有 Key 参与 LFU 淘汰                        |
| volatile-lfu (4.0+)       | 仅有过期时间 Key 参与 LFU 淘汰                |
+---------------------------+----------------------------------------------+

=== LRU 近似实现 ===
精确 LRU 需要双向链表 + HashMap, 内存开销大

Redis 近LRU (采样淘汰):
  1. 随机抽取 maxmemory-samples (默认5) 个 Key
  2. 淘汰其中空闲时间最长的 Key
  3. 写入时重复直到内存满足要求

每个 Key 在对象中保存一个 24-bit LRU 时钟:
  - lru: 最后访问时间 (精确到分钟)
  - 淘汰时比较 LRU 时钟值
  - 采样越多越接近精确 LRU (maxmemory-samples=10 就很接近)

=== LFU 实现 (Redis 4.0+) ===
LRU 的问题: 偶尔访问的大 Key 排挤频繁访问的热 Key

LFU 使用 24-bit 字段:
  +---------------16-bit--------------+----8-bit----+
  |       最后访问时间 (分钟)          | 对数访问频率 |
  +----------------------------------+--------------+

访问频率使用对数计数:
  - 每次访问: counter += 1 (但使用概率性增长, 防止溢出)
  - 随时间衰减: counter = counter - (now - lastTime) * decayFactor
```

### 3. 过期策略 (Expiration)

```
=== 三种过期删除方式 ===

1. 被动删除 (Lazy):
   访问 Key 时检查是否过期
   过期则删除并返回 nil
   优点: CPU友好
   缺点: 过期但未被访问的 Key 占用内存

2. 定期删除 (Active):
   每秒运行 10 次 (hz 参数控制)
   每次随机抽取 20 个 Key 检查
   如果过期比例 > 25%, 继续循环直到 < 25% 或超时
   单次循环时间上限: 25ms

3. 定时删除:
   为每个过期 Key 创建定时器
   过期时立即删除
   不推荐: 定时器开销大, CPU 密集

Redis 实际: 被动删除 + 定期删除 (折中方案)
```

### 4. 大 Key 问题与解决

```
=== 大 Key 的危害 ===
  - 内存分布不均 (集群中某些节点 OOM)
  - 阻塞: DEL 大 Key O(N), 主线程阻塞
  - 网络带宽: 传输大 Value
  - 主从复制: 大 Key 的同步时间长
  - 迁移: Redis Cluster Reshard 时大 Key 迁移慢

=== 解决方法 ===

方案1: UNLINK (异步删除, Redis 4.0+)
  UNLINK bigkey
  // 后台线程异步释放内存, 不阻塞主线程

方案2: 分批删除
  // 对于 Hash
  HSCAN bigHash 0 COUNT 100  // 分批扫描
  HDEL bigHash field1 field2 ... // 分批删除

方案3: 业务优化
  - 拆分大 Key 为多个小 Key
  - 压缩 Value (Snappy/LZ4 压缩字符串)
  - 使用 Hash 结构代替多个 String key

方案4: lazyfree 配置
  lazyfree-lazy-eviction yes     // 淘汰时异步删除
  lazyfree-lazy-expire yes       // 过期时异步删除
  lazyfree-lazy-server-del yes   // 其他隐式DEL用UNLINK
```

### 5. 缓存一致性 (Cache-Aside Pattern)

```
=== 缓存与数据库一致性 ===

模式: Cache-Aside (旁路缓存)

读流程:
  data = cache.get(key)
  if data == null:
      data = db.query(key)
      db.query(key) -> data
      cache.set(key, data, ttl)
  return data

写流程 (先更新DB, 再删缓存):
  db.update(key, newValue)      // ① 先写 DB
  cache.delete(key)             // ② 再删缓存
  // 为什么是删缓存而不是更新缓存?
  // 答: 并发写缓存可能覆盖; 删缓存最简单, 下一次读会重建

=== 为什么是 "删缓存" 而不是 "更新缓存"？ ===

并发写场景:
  T1: Write A=1 -> DB A=1
  T2: Write A=2 -> DB A=2
  T2: cache.set(A=2)
  T1: cache.set(A=1)  // 如果 T1 先执行完 DB但后更新缓存
  -> 缓存中是旧值 A=1, DB 中是新值 A=2 (不一致!)

如果改用删缓存:
  T1: DB A=1 -> cache.del(A)
  T2: DB A=2 -> cache.del(A)
  -> 缓存被删除, 下次读会从 DB 加载新值

=== 延迟双删 (最终一致性增强) ===
  db.update(key, newValue)
  cache.delete(key)               // 第一次删除
  sleep(几百ms)                    // 等待其它线程可能写脏缓存
  cache.delete(key)               // 第二次删除
  // 适用于要求较高一致性的场景; sleep 时间 > 读+重建缓存时间

=== 使用消息队列保证最终一致 ===
  db.update(key, newValue)
  mq.send({action: "deleteCache", key: key})

  Consumer:
    cache.delete(key)             // 异步删除, 保证最终一致
    // 如果删除失败, 消息队列重试
```

### 6. 内存优化

```
=== 内存回收 ===
  jemalloc: Redis 默认内存分配器
  - 减少内存碎片
  - 内存统计: used_memory / used_memory_rss
  - 碎片率: mem_fragmentation_ratio = rss / used_memory
  - 碎片率 > 1.5 考虑重启或 activedefrag

=== 内存自动碎片整理 (Redis 4.0+) ===
  activedefrag yes
  active-defrag-ignore-bytes 100mb   // 碎片 >100MB 开始
  active-defrag-threshold-lower 10   // 碎片率 >10% 开始
  active-defrag-cycle-min 5          // CPU 占比 >5%
  active-defrag-cycle-max 75         // CPU 占比 <75%

=== 共享整数对象 (Redis 3.0-) ===
  0-9999 的整数对象全局共享, 节省内存
  4.0+ 因线程安全原因移除(改为LFU/LRU字段使对象可变)

=== 内存优化实践 ===
  1. 使用 hash-max-ziplist-* 限制, 小Hash用压缩列表
  2. 短 Key 名 (但要可读)
  3. 合适的淘汰策略 (allkeys-lru)
  4. 定期清理无用数据
  5. 考虑 SSD 缓存方案 (如 Intel Optane PMem)
```

---

## 扩展性与高可用

### 1. Sentinel 哨兵模式

```
+----------------------------------------------------------+
|                    Sentinel 集群 (至少3节点)               |
|                                                           |
|  +-----------+   +-----------+   +-----------+            |
|  | Sentinel1 |   | Sentinel2 |   | Sentinel3 |            |
|  |  :26379   |   |  :26379   |   |  :26379   |            |
|  +-----+-----+   +-----+-----+   +-----+-----+            |
|        |               |               |                  |
|        +------+--------+------+--------+                  |
|               |               |                           |
+----------------------------------------------------------+
                |               |
                v               v
+-------------------------+   +-------------------------+
|    Master (6379)        |   |    Slave (6379)         |
|  +------------------+   |   |  +------------------+   |
|  | 被 Sentinel 监控   |   |   | 被 Sentinel 监控   |   |
|  +------------------+   |   |  +------------------+   |
+-------------------------+   +-------------------------+

Sentinel 功能:
  1. 监控 (Monitoring): 持续检查 Master/Slave 是否在线
  2. 通知 (Notification): API 通知运维人员
  3. 自动故障转移 (Automatic Failover):
     - 主观下线 (SDOWN): 单个 Sentinel 认为节点不可达
     - 客观下线 (ODOWN): quorum 个 Sentinel 认为节点不可达
     - 选举 Leader Sentinel 执行切换
     - 从 Slaves 中选出新 Master (replica-priority 最高的)
     - 将其他 Slave 改为复制新 Master
     - 旧 Master 恢复后改为 Slave
  4. 配置提供者 (Configuration Provider):
     Client 询问 Sentinel 获取当前 Master 地址

故障转移决策:
  quorum: 认为下线需要的最少 Sentinel 数量
  选出新 Master 的优先级:
    1. replica-priority (越小越优先)
    2. 复制偏移量最大 (数据最新)
    3. runid 字典序最小
```

### 2. Redis Cluster 数据分片

```
=== 槽位迁移流程 ===

1. 源节点设置为 MIGRATING 状态 (对于目标槽位)
2. 目标节点设置为 IMPORTING 状态 (对于目标槽位)
3. 迁移单个 Key:
   MIGRATE target-host target-port key 0 1000
   (原子操作: dump key -> 发送 -> restore -> del source)
4. 批量迁移: CLUSTER GETKEYSINSLOT <slot> <count>
5. 通知所有节点更新槽位映射

槽迁移过程中的请求处理:
  - 源节点 MIGRATING:
    - Key 存在 -> 正常处理
    - Key 不存在 -> 返回 ASK 重定向 (引导到目标节点)
  - 目标节点 IMPORTING:
    - 正常收到命令 -> 正常执行
    - 没有但需要 -> 返回 MOVED (因为客户端的槽位表还记得源节点)

=== Hash Tag ===
  key = "{user:123}:profile"
  key = "{user:123}:orders"

  CRC16("user:123") % 16384
  -> 两个 Key 落在同一个 Slot -> 可以执行多 Key 操作

=== Smart Client 路由 ===
+----------------------------+
|       Smart Client         |
|                            |
| +----------+               |
| | Slot Map |  <-- Slot缓存  |
| | Cache    |               |
| +----------+               |
|                            |
| 1. 计算 CRC16(key) % 16384 |
| 2. 查Slot Map获取目标节点    |
| 3. 发送命令                 |
| 4. MOVED -> 更新Slot Map    |
|    ASK -> 单次重定向         |
+----------------------------+
```

### 3. 缓存穿透 / 击穿 / 雪崩

```
=== 缓存穿透 (Cache Penetration) ===
描述: 查询不存在的数据, 缓存和DB都没有
危害: 大量请求穿透到DB
解决:
  1. 布隆过滤器 (Bloom Filter):
     将所有存在的 Key 写入 Bloom Filter
     查询前先检查 Bloom Filter
     不存在 -> 直接返回 null

  2. 缓存空值:
     cache.set(key, null, SHORT_TTL)  // 缓存空值, 短TTL
     缺点: 恶意攻击者用不同Key绕过

  3. 接口层校验: 参数校验 + 限流

=== 缓存击穿 (Hotspot Invalid) ===
描述: 热点 Key 过期, 大量请求同时打到DB
危害: DB瞬时高压
解决:
  1. 互斥锁 (Mutex Lock):
     if cache.get(key) == null:
         if lock.acquire(key_lock):
             data = db.query(key)
             cache.set(key, data, ttl)
             lock.release(key_lock)
         else:
             sleep(50ms) -> 重试

  2. 永不过期 (逻辑过期):
     物理上不设 TTL
     使用异步线程定期更新 Value
     读取时发现逻辑过期, 返回旧值, 异步更新

=== 缓存雪崩 (Cache Avalanche) ===
描述: 大量 Key 同时过期 或 缓存服务宕机
危害: DB瞬时高压甚至宕机
解决:
  1. TTL 加随机值:
     TTL = baseTTL + random(0, 300)  // 加5分钟随机

  2. 多级缓存:
     本地缓存 (Caffeine) -> Redis -> DB

  3. 限流 + 降级:
     缓存不可用时, 服务降级返回默认值
     Sentinel 限流保护 DB

  4. 高可用: Redis Cluster + Sentinel, DB 读写分离

  5. 缓存预热: 提前加载热点数据
```

### 4. 监控指标

```
关键指标:

性能:
  - instantaneous_ops_per_sec: 每秒操作数
  - latency_percentiles_usec: 延迟分位数
  - connected_clients: 连接数
  - blocked_clients: 阻塞客户端数
  - used_cpu_sys / used_cpu_user: CPU 占用

内存:
  - used_memory / used_memory_rss
  - mem_fragmentation_ratio: 碎片率 (>1.5需关注)
  - maxmemory: 最大内存
  - evicted_keys: 淘汰 Key 数
  - expired_keys: 过期 Key 数

持久化:
  - rdb_last_bgsave_status / rdb_last_bgsave_time_sec
  - aof_enabled / aof_last_write_status / aof_current_size

复制:
  - master_repl_offset / slave_repl_offset: 复制延迟
  - master_link_status: up/down
  - connected_slaves: 从节点数

集群:
  - cluster_state: ok/fail
  - cluster_known_nodes: 集群节点数
  - cluster_slots_ok / cluster_slots_fail

Key 分布:
  - 总 Key 数
  - 大 Key 检测: redis-cli --bigkeys
  - 热点 Key 检测: redis-cli --hotkeys (Redis 4.0+)
```

---

## 总结

设计分布式缓存需要权衡以下核心维度：

| 维度 | 核心决策 |
|------|----------|
| **数据结构** | String/List/Set/Hash/ZSet + 内部编码优化 (ZipList/SDS/SkipList) |
| **性能** | 单线程内存操作 + epoll/kqueue 多路复用 + Pipeline 批量 |
| **持久化** | RDB 快照 + AOF 日志 + 混合持久化, 根据 RPO/RTO 选择 |
| **高可用** | 主从复制 + Sentinel 自动故障转移 |
| **扩展** | Redis Cluster 16384 槽位分片 + Gossip 协议 + Smart Client |
| **缓存策略** | LRU/LFU 近似淘汰 + 过期 (懒删除+定期删除) |
| **一致性** | Cache-Aside + 延迟双删 + 最终一致性 |

关键面试问答：
1. **Redis为什么这么快？** — 纯内存操作 + 单线程无锁 + epoll多路复用 + 高效数据结构(SDS/SkipList)
2. **如何保证缓存与DB一致性？** — Cache-Aside(先更新DB再删缓存) + 延迟双删 + 订阅Binlog异步删缓存
3. **缓存穿透/击穿/雪崩怎么解决？** — 穿透用布隆过滤器；击穿用互斥锁+永不过期；雪崩用随机TTL+多级缓存+限流
4. **Redis Cluster vs Sentinel？** — Cluster 用于数据分片水平扩展, Sentinel 用于高可用主从接管, 两者可结合
5. **RDB vs AOF怎么选？** — RDB 恢复快(适合备份), AOF 数据安全(适合高可靠性), 4.0+建议混合持久化
6. **Redis内存淘汰策略选哪个？** — 一般 allkeys-lru；有点击率统计需求 allkeys-lfu；缓存不能丢不要淘汰 volatile-ttl
