# LRU Cache — 考点分析与解题思路

## 考点分析

1. **数据结构设计**：题目要求 `get`/`put` 平均 O(1)，单靠数组（查找 O(n)）或单靠链表（查找 O(n)）都不行。核心是「哈希表（O(1) 查找）+ 双向链表（O(1) 增删 + 维护顺序）」的组合。
2. **使用顺序维护**：LRU 的本质是「按最近使用时间排序」，需要能在 O(1) 内把任意节点移到头部（最近使用）以及删除尾部（最久未使用）。双向链表天然支持。
3. **TypeScript 技巧**：`Map` 保持**插入顺序**，因此可用单 `Map` 实现等价效果——`get` 时删除再重插刷新顺序，`put` 超容量时删除 `map.keys().next().value`（第一个 key 即最久未使用）。面试先说「哈希 + 双向链表」的经典思路，再补充 `Map` 的简洁实现。
4. **边界**：容量为 1、重复 `put` 同一 key（更新不增加数量）、`get` 不存在的 key。

## 解题思路

### 方案 A：Map（插入顺序）

- 用 `Map<number, number>`，其迭代顺序 = 插入顺序，且「重新 set」会把它移到末尾。
- `get(key)`：不存在返回 -1；存在则 `delete` 后 `set` 同值，刷新为最近使用。
- `put(key, value)`：
  - 若存在：先 `delete`（刷新顺序）；
  - 否则若 `size >= capacity`：删除第一个 key（`this.map.keys().next().value`，最久未使用）；
  - 最后 `set(key, value)`。

### 方案 B：哈希表 + 双向链表（手写）

- 维护哨兵 `head`/`tail`，最近使用靠近 `head`，最久未使用靠近 `tail`。
- 哈希表 `key -> node`。
- `get`/`put` 命中时把节点移到 `head`；超容量删除 `tail.prev` 并在哈希表中移除。

## 复杂度

- 时间：`get` / `put` 均 O(1)。
- 空间：O(capacity)。

## 参考代码（Map 实现）

```ts
class LRUCache {
  private capacity: number;
  private map = new Map<number, number>();

  constructor(capacity: number) {
    this.capacity = capacity;
  }

  get(key: number): number {
    if (!this.map.has(key)) return -1;
    const value = this.map.get(key)!;
    this.map.delete(key);          // 刷新为最近使用
    this.map.set(key, value);
    return value;
  }

  put(key: number, value: number): void {
    if (this.map.has(key)) {
      this.map.delete(key);        // 更新也需刷新顺序
    } else if (this.map.size >= this.capacity) {
      const lruKey = this.map.keys().next().value as number;
      this.map.delete(lruKey);     // 淘汰最久未使用
    }
    this.map.set(key, value);
  }
}
```

## 参考代码（哈希表 + 双向链表，手写）

```ts
class DLinkedNode {
  key = 0;
  value = 0;
  prev: DLinkedNode | null = null;
  next: DLinkedNode | null = null;
}

class LRUCache {
  private capacity: number;
  private cache = new Map<number, DLinkedNode>();
  private head = new DLinkedNode();   // 哨兵：最近使用
  private tail = new DLinkedNode();   // 哨兵：最久未使用

  constructor(capacity: number) {
    this.capacity = capacity;
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  private remove(node: DLinkedNode) {
    node.prev!.next = node.next;
    node.next!.prev = node.prev;
  }

  private addToHead(node: DLinkedNode) {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next!.prev = node;
    this.head.next = node;
  }

  private moveToHead(node: DLinkedNode) {
    this.remove(node);
    this.addToHead(node);
  }

  private removeTail(): DLinkedNode {
    const node = this.tail.prev!;
    this.remove(node);
    return node;
  }

  get(key: number): number {
    const node = this.cache.get(key);
    if (!node) return -1;
    this.moveToHead(node);
    return node.value;
  }

  put(key: number, value: number): void {
    const node = this.cache.get(key);
    if (node) {
      node.value = value;
      this.moveToHead(node);
    } else {
      const newNode = new DLinkedNode();
      newNode.key = key;
      newNode.value = value;
      this.cache.set(key, newNode);
      this.addToHead(newNode);
      if (this.cache.size > this.capacity) {
        const tail = this.removeTail();
        this.cache.delete(tail.key);
      }
    }
  }
}
```

## 追问 / Follow-ups

1. **多进程/分布式 LRU** 怎么做？→ 用 Redis：`SET` + `ZSET`（score 存时间戳）或直接依赖 Redis 的 `maxmemory-policy allkeys-lru`。
2. 改成 **LFU**（最不经常使用）？→ 额外维护访问频率计数 + 按频率分组的多链表。
3. 手写双向链表版为什么要用哨兵节点？→ 省去对头/尾为 `null` 的判断，避免边界分支。
