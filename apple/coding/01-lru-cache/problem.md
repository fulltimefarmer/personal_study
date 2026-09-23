# LRU Cache · LRU 缓存

- **LeetCode:** 146
- **难度 Difficulty:** Medium
- **标签 Topics:** 设计 / 哈希表 / 双向链表 / Design / Hash Table / Doubly-Linked List
- **苹果频率:** 最高频（Apple #1）

## 题干（中文）

设计并实现一个遵循「最近最少使用 (Least Recently Used, LRU)」约束的缓存。实现 `LRUCache` 类：

- `LRUCache(capacity: number)`：用正数容量初始化缓存。
- `get(key: number): number`：若 `key` 存在，返回其值并把它标记为最近使用；否则返回 `-1`。
- `put(key: number, value: number): void`：若 `key` 存在，更新其值；否则插入新键值对。若插入后键的数量超过容量，则淘汰「最久未使用」的键。

`get` 与 `put` 必须平均在 **O(1)** 时间内完成。

## Problem Statement (English)

Design and implement a data structure for a Least Recently Used (LRU) cache. Implement `LRUCache`:

- `LRUCache(capacity: number)`: initialize with a positive capacity.
- `get(key: number): number`: return the value if it exists and mark it most recently used; otherwise `-1`.
- `put(key: number, value: number): void`: update the value if it exists; otherwise insert. If inserting exceeds capacity, evict the least recently used key.

`get` and `put` must run in **O(1)** average time.

## 示例 / Example

```ts
const cache = new LRUCache(2);
cache.put(1, 1);   // 缓存为 {1=1}
cache.put(2, 2);   // 缓存为 {1=1, 2=2}
cache.get(1);      // 返回 1（1 变为最近使用）
cache.put(3, 3);   // 淘汰 key 2，缓存为 {1=1, 3=3}
cache.get(2);      // 返回 -1（未找到）
cache.put(4, 4);   // 淘汰 key 1，缓存为 {4=4, 3=3}
cache.get(1);      // 返回 -1
cache.get(3);      // 返回 3
cache.get(4);      // 返回 4
```

## 约束 / Constraints

- `1 <= capacity <= 3000`
- `0 <= key <= 10^4`
- `0 <= value <= 10^5`
- 最多调用 `2 * 10^5` 次 `get` / `put`
