# 题目 3：带 TTL 的内存键值存储

## 题目描述

设计并实现一个**支持 TTL（生存时间）的内存键值存储系统**。

要求实现以下功能：

- `void put(K key, V value)` —— 存储一个**永不过期**的键值对。
- `void put(K key, V value, long ttlMillis)` —— 存储一个带 TTL 的键值对，超时后自动失效。
- `V get(K key)` —— 获取 key 对应的值。如果 key **不存在**或**已过期**，返回 `null`，同时删除过期条目。
- `V remove(K key)` —— 主动删除一个 key。
- `int size()` —— 返回当前**未过期**条目的数量。

### 进阶要求

- 过期条目采用**惰性删除**（访问时检查并清理）。
- 同时提供**定期后台清理机制**，防止永不访问的 key 造成内存泄漏。
- 整个存储必须是**线程安全**的。

## 示例

```java
KVStore<String, String> kv = new KVStore<>(500);  // 500ms 清理间隔
kv.start();

kv.put("session", "abc123", 1_000);   // 1 秒后过期
kv.put("config",  "prod");           // 永不过期

kv.get("session");  // → "abc123"
kv.get("config");   // → "prod"

Thread.sleep(1_100);
kv.get("session");  // → null (已过期)
kv.get("config");   // → "prod" (未过期)
```

## 解题思路

### 1. 过期策略对比

| 策略 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **惰性删除** | 访问时才检查是否过期 | 实现简单，CPU 友好 | 不访问的 key 永远不会被清理（内存泄漏） |
| **定期删除** | 定时扫描全部 key 并删除过期条目 | 避免内存泄漏 | 定时扫描有 CPU 开销 |
| **混合策略**（推荐） | 惰性 + 定期结合 | 兼顾性能与内存 | 实现稍复杂 |

**本实现采用混合策略**：惰性删除覆盖所有 `get`/`remove` 操作，定期后台扫描清理遗漏的过期 key。

### 2. 核心数据结构

```
┌─────────────────────────────────────────────────────────┐
│                    KVStore<K, V>                         │
│                                                          │
│  ConcurrentHashMap<K, Entry<V>> store                   │
│  │                                                       │
│  │  ┌──────────────┐                                     │
│  └──► Entry<V>      │                                     │
│       ├── value     │                                     │
│       └── expiryTime (Long.MAX_VALUE 表示永不过期)        │
│                                                          │
│  ScheduledExecutorService scheduler                      │
│  └── cleanupTask (定时扫描并移除过期 Entry)               │
└─────────────────────────────────────────────────────────┘
```

### 3. 关键设计细节

**过期时间存储**
- 每个 `Entry` 存储**绝对过期时间戳**（`System.currentTimeMillis() + ttlMillis`）而非 TTL 秒数。
- `Long.MAX_VALUE` 作为"永不过期"的特殊标记，统一比较逻辑。

**惰性删除——CAS 原子删除**
```java
public V get(K key) {
    Entry<V> entry = store.get(key);
    if (entry == null) return null;
    if (entry.isExpired()) {
        store.remove(key, entry);  // 条件删除：仅当 value 仍为该 entry 时才删除
        return null;
    }
    return entry.value;
}
```
使用 `ConcurrentHashMap.remove(key, value)`（带值匹配的原子删除），防止在检查过期和删除之间被其他线程修改。

**后台定期清理**
- 使用 `ScheduledExecutorService` 的 `scheduleWithFixedDelay`，以固定间隔执行。
- 清理线程设为**守护线程**（daemon），确保 JVM 退出时不阻塞。
- `shutdown()` 方法使用 `awaitTermination` 优雅等待任务完成后关闭。

### 4. 生命周期管理

```
  ┌───────┐     ┌─────────┐     ┌──────────┐
  │ new() │────►│ start() │────►│ 运行中... │
  └───────┘     └─────────┘     └─────┬────┘
                                      │
                                 shutdown()
                                      │
                                      ▼
                               ┌──────────┐
                               │ 安全关闭  │
                               └──────────┘
```

### 5. 复杂度分析

- **时间复杂度**：`get`、`put`、`remove` 均近似 O(1)（ConcurrentHashMap 分摊）。
- **空间复杂度**：O(n)，n 为存储的条目数。

## 考察维度

- **生产工程实践**：内存管理、后台线程生命周期、资源释放。
- **并发编程**：`ConcurrentHashMap` 的正确使用，原子操作，避免竞态条件。
- **代码质量**：Builder/配置模式、职责分离（存储 vs 过期逻辑）。
- **技术深度**：TTL 策略权衡、时间戳比较、GC 压力考量。
