# In-Memory Cache with TTL — 考点分析与解题思路

## 考点分析

1. **过期元数据**：每个条目存 `{ value, expiresAt }`，`expiresAt = Date.now() + ttlMs`。判断过期只需比较当前时间与 `expiresAt`。
2. **惰性过期（lazy）**：不在后台 `setInterval` 扫描，而是在 `get`/`has` 命中时检查是否过期，过期则 `delete` 并返回未命中。实现简单、无后台开销，但过期键会在「无人访问」时占用内存（通常可接受）。
3. **`size` 语义**：惰性过期下 `size` 直接返回 `Map.size` 会偏大（含过期键）。需在 `size` 访问时也做一次清理，或在 `get`/`has` 中顺带清掉（本实现按「访问时清理」处理）。
4. **主动过期（active）对比**：可加后台定时扫描或「按到期时间排序的最小堆」，用于内存敏感场景。

## 解题思路

- `store = new Map<string, { value: unknown; expiresAt: number }>()`。
- `set`：写入 `{ value, expiresAt: Date.now() + ttlMs }`。
- `get`：取条目；不存在返回 `undefined`；`Date.now() >= expiresAt` 则 `delete` 并返回 `undefined`；否则返回值。
- `has`：复用 `get(key) !== undefined`。
- `delete` / `clear`：直接转发 `Map` 操作。
- `size`：先清掉所有过期键再返回 `Map.size`（或提供独立的 `prune()`）。

## 复杂度

- `set`/`get`/`has`/`delete`：O(1)。
- `size`：O(n)（需扫描清理过期键）；若不要求严格精确可 O(1) 返回近似值。

## 参考代码

```ts
class TTLCache {
  private store = new Map<string, { value: unknown; expiresAt: number }>();

  set(key: string, value: unknown, ttlMs: number): void {
    this.store.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  get(key: string): unknown {
    const entry = this.store.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.expiresAt) {
      this.store.delete(key);
      return undefined;
    }
    return entry.value;
  }

  has(key: string): boolean {
    return this.get(key) !== undefined;
  }

  delete(key: string): boolean {
    return this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }

  private prune(): void {
    const now = Date.now();
    for (const [k, v] of this.store) {
      if (now >= v.expiresAt) this.store.delete(k);
    }
  }

  get size(): number {
    this.prune();
    return this.store.size;
  }
}
```

## 追问 / Follow-ups

1. **内存占用与过期键残留？**→ 惰性过期会残留无人访问的过期键；可加「后台定时 prune」或「容量上限 + LRU 淘汰」。
2. **主动过期怎么设计？**→ `setInterval` 定期 prune，或用「按 expiresAt 排序的最小堆 + 定时器触发最早到期项」。
3. **分布式缓存**？→ 用 Redis：`SET key value EX ttl` 原生支持 TTL；或 `SET + PEXPIRE`。
4. **缓存穿透/击穿/雪崩**？→ 空值缓存、互斥锁重建、过期时间加随机抖动（呼应退避题的 jitter 思想）。
