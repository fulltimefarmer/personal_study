# 题目：Redis 五种基本数据类型

## 问题
请详细说明 Redis 五种基本数据类型（String、Hash、List、Set、ZSet）的使用场景与底层实现，包括各自的编码方式和适用条件。

## 考点
- 五种数据类型及适用场景
- 底层数据结构（SDS、ziplist、listpack、quicklist、skiplist、hashtable、intset）
- 编码切换的条件（Redis 的 `object encoding` 机制）
- 实际业务中的使用案例

## 解答

### 一、Redis 核心数据结构总览

```
Redis 对外数据类型              底层编码（内部实现）

String           →  int / embstr / raw
Hash             →  ziplist / listpack / hashtable
List             →  quicklist
Set              →  intset / hashtable
ZSet             →  ziplist / listpack / skiplist + hashtable
```

Redis 采用"对象"系统，每种类型有至少两种底层编码，自动根据数据大小和元素个数切换。

---

### 二、String（字符串）

**特点**：最简单的类型，可以存任何二进制安全的数据（最大 512MB）。

**底层实现**：

| 编码 | 条件 | 说明 |
|------|------|------|
| `int` | 值是整数且长度 ≤ 20 位 | 直接存整数以节省内存 |
| `embstr` | 值 ≤ 44 字节 | 一次分配内存（连续），只读时高效 |
| `raw` | 值 > 44 字节 | 两次分配内存，可修改 |

**SDS（Simple Dynamic String）**：

```c
struct sdshdr {
    int len;    // 字符串长度
    int free;   // buf 剩余空间
    char buf[]; // 字符串内容
};
```

**为什么不用 C 原生字符串**：
- C 字符串不记录长度 → 每次 `strlen` 是 O(n)，SDS 是 O(1)
- C 字符串可能缓冲区溢出 → SDS 有 `free` 空间预分配
- C 字符串遇 `\0` 截断 → SDS 是二进制安全的
- SDS 有惰性空间释放和预分配，减少内存重分配

**使用场景**：

| 场景 | 命令示例 |
|------|---------|
| 缓存 JSON 字符串 | `SET user:1 '{"name":"Tom","age":20}'` |
| 计数器 / 分布式限流 | `INCR page_view:article:123` |
| 分布式锁 | `SET lock:order:456 uuid NX EX 30` |
| Session 共享 | `SET session:token:abc '{"userId":1}' EX 1800` |

```java
// Java (Jedis)
jedis.set("user:1", "{\"name\":\"Tom\"}");
jedis.incr("counter");

// TypeScript (ioredis)
await redis.set("user:1", JSON.stringify({ name: "Tom" }));
await redis.incr("counter");
```

---

### 三、Hash（哈希）

**特点**：键值对集合，适合存对象。

**底层实现**：

| 编码 | 条件（Redis 7+） | 说明 |
|------|------------------|------|
| `listpack` | 元素少、value 短时 | 连续内存，更节省空间 |
| `hashtable` | 元素多或 value 长时 | 标准哈希表 |

**使用场景**：

| 场景 | 命令示例 |
|------|---------|
| 对象缓存（可部分更新） | `HSET user:1 name "Tom" age 20`；`HGET user:1 name` |
| 购物车 | `HSET cart:user:1 item:123 2`（商品 ID → 数量） |
| 短链接映射 | `HSET shorturl:abc "url" "https://...", "clicks" 100` |

**Hash 比 String 存 JSON 的优势**：
- 可以单独读写某个字段（`HGET` / `HINCRBY`），不用整体序列化/反序列化
- 如果字段很小，`listpack` 编码更省内存

```java
// Java
Map<String, String> user = new HashMap<>();
user.put("name", "Tom");
user.put("age", "20");
jedis.hset("user:1", user);

// 单独更新一个字段
jedis.hincrBy("user:1", "age", 1);
```

```typescript
// TypeScript
await redis.hset("user:1", "name", "Tom", "age", "20");
await redis.hget("user:1", "name");
await redis.hincrby("user:1", "age", 1);
```

---

### 四、List（列表）

**特点**：有序、可从两端操作的双向链表。

**底层实现**：

| 版本 | 编码 | 说明 |
|------|------|------|
| Redis 3.2+ | `quicklist` | 结合了 linkedlist 和 ziplist 的优点 |

**quicklist**：一个双向链表，每个节点是一个 ziplist/listpack（压缩列表），多个元素压缩存。

```
quicklist 结构：

head → [ziplist: A B C] ⇄ [ziplist: D E F] ⇄ [ziplist: G H I] ← tail
         ↑ 一个节点存 3 个元素
```

**使用场景**：

| 场景 | 命令示例 |
|------|---------|
| 消息队列（简单） | `LPUSH queue:task "job1"` + `RPOP queue:task` |
| 阻塞队列（BRPOP） | `BRPOP queue:task 0`（等待新消息） |
| 最新动态/时间线 | `LPUSH timeline:user1 "post1"` + `LRANGE timeline:user1 0 9` |
| Stack 栈 | `LPUSH + LPOP` |

```java
// 阻塞队列（可靠消费者需实现 ACK，Redis 5+ 推荐用 Stream）
jedis.lpush("task_queue", "job1", "job2");
// BRPOP 阻塞等待（0 为无限超时）
List<String> result = jedis.brpop(0, "task_queue");
```

```typescript
// TypeScript
await redis.lpush("timeline:user:1", "post:1", "post:2");
const recent = await redis.lrange("timeline:user:1", 0, 9);
```

---

### 五、Set（集合）

**特点**：无序无重复，支持交/并/差集运算。

**底层实现**：

| 编码 | 条件 | 说明 |
|------|------|------|
| `intset` | 所有元素都是整数，且数量少 | 有序整数数组（节省内存） |
| `hashtable` | 非整数元素或数量多 | 标准哈希表（value 为 NULL） |

**使用场景**：

| 场景 | 命令示例 |
|------|---------|
| 点赞集合 | `SADD like:article:1 userId:100`；`SCARD like:article:1`（点赞数） |
| 共同好友/交集 | `SINTER friends:user1 friends:user2` |
| 标签 | `SADD article:1:tags "Redis" "DB"` |
| 随机元素（抽奖） | `SRANDMEMBER lottery:pool 1`（不删除）；`SPOP lottery:pool 1`（删除） |
| 去重 | `SADD unique_visitors:today "ip:1.2.3.4"` |

```java
Set<String> mutualFriends = jedis.sinter("friends:user1", "friends:user2");

// 抽奖：随机取一个且移除
String winner = jedis.spop("lottery_pool");
```

```typescript
const common = await redis.sinter("friends:user1", "friends:user2");
const isMember = await redis.sismember("like:article:1", "userId:100");
```

---

### 六、Sorted Set（有序集合，ZSet）

**特点**：每个元素关联一个 score（分数），按 score 排序。既是 Set（元素唯一）又是有序的。

**底层实现**：

| 编码 | 条件 | 说明 |
|------|------|------|
| `listpack` | 元素少、value 短 | 连续内存 |
| `skiplist + hashtable` | 默认 | 跳表负责按 score 排序，哈希表负责快速按元素定位 |

**跳表（Skip List）原理**：

```
Level 2:  [1] ────────→ [15] ─────────────→ [50]
Level 1:  [1] → [8] → [15] → [30] → [40] → [50]
Level 0:  [1]→[3]→[8]→[12]→[15]→[25]→[30]→[36]→[40]→[48]→[50]
          ← 底层双向链表，上面是多层"快速通道"

查找复杂度：平均 O(log n)
层数：随机决定（每次插入抛硬币决定升多少层）
```

**为什么不用红黑树**：跳表实现更简单，且支持范围查询（红黑树需要中序遍历，跳表直接在底层链表上遍历即可）。

**使用场景**：

| 场景 | 命令示例 |
|------|---------|
| 排行榜 | `ZADD leaderboard:game1 1000 "playerA" 950 "playerB"`；`ZREVRANGE leaderboard:game1 0 9 WITHSCORES` |
| 延时队列 | `ZADD delay_queue <future_timestamp> "task:1"`；`ZRANGEBYSCORE delay_queue 0 <now> LIMIT 0 1` |
| 带权重的标签 | `ZINCRBY hot_tags 1 "Redis"`（每次搜索加 1） |
| 滑动窗口限流 | score 用时间戳，ZREMRANGEBYSCORE 删旧数据 |

```java
// 排行榜：写入分数
jedis.zadd("leaderboard", 1000, "playerA");

// 查询 top 10（倒序，分数高的在前）
Set<String> top10 = jedis.zrevrange("leaderboard", 0, 9);

// 查询某个玩家的排名（0-based，需 +1）
Long rank = jedis.zrevrank("leaderboard", "playerA"); // 1000 分的排第 0

// 延时队列
long now = System.currentTimeMillis();
jedis.zadd("delay_queue", now + 60000, "task:1"); // 1 分钟后执行
Set<String> ready = jedis.zrangeByScore("delay_queue", 0, now);
```

```typescript
// TypeScript
await redis.zadd("leaderboard", 1000, "playerA", 950, "playerB");
const top10 = await redis.zrevrange("leaderboard", 0, 9, "WITHSCORES");
const rank = await redis.zrevrank("leaderboard", "playerA");
```

---

### 七、编码切换的触发条件

Redis 自动根据数据大小切换内部编码，平衡内存和性能：

| 类型 | 编码 | 小数据编码策略 | 切换条件（可配置） |
|------|------|--------------|-------------------|
| String | int/embstr/raw | embstr | value > 44 字节 → raw |
| Hash | listpack / hashtable | listpack | entries > 512 或 value > 64B |
| List | quicklist | quicklist | — |
| Set | intset / hashtable | intset | entries > 512 或非整数 |
| ZSet | listpack / skiplist | listpack | entries > 128 或 member > 64B |

**查看对象的编码**：
```bash
OBJECT ENCODING key
# 返回: "embstr" / "int" / "quicklist" / "hashtable" / "skiplist" 等
```

---

### 八、不常用但重要的类型补充

| 类型 | 说明 | 典型场景 |
|------|------|---------|
| **Bitmap** | 位图（实际是 String 的位操作） | 签到打卡、用户在线状态 |
| **HyperLogLog** | 基数统计（误差 0.81%） | UV 统计 |
| **GEO** | 地理位置（实际基于 ZSet） | 附近的人、配送范围 |
| **Stream** | 消息流（Redis 5.0+） | 可靠消息队列（消费者组 + ACK） |

```bash
# GEO 示例
GEOADD locations 116.397 39.908 "Beijing" 121.473 31.230 "Shanghai"
GEORADIUS locations 116.4 39.9 1000 km WITHDIST

# HyperLogLog 示例
PFADD uv:page:20240101 user1 user2 user3
PFCOUNT uv:page:20240101   # → 3
```

---

## 总结
String 最通用，Hash 适合对象缓存和部分更新，List 用作消息队列/时间线，Set 用于去重和交/并/差集，ZSet 是排行榜首选。每种类型都有至少两种底层编码，Redis 自动在小数据时用压缩/连续内存编码（listpack/ziplist/intset）节省内存，在数据量大时切换到标准结构（hashtable/skiplist）保证性能。理解编码切换是 Redis 性能优化的关键。
