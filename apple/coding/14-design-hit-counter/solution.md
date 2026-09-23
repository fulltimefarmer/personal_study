# Design Hit Counter — 考点分析与解题思路

## 考点分析

1. **数据流 + 滑动时间窗口**：点击是「按时间递增」到达的流，需要在任意时刻查询过去 300 秒的计数。核心是「淘汰过期数据」。
2. **单调性可利用**：因为调用时间戳单调递增，队列中保存的时间戳天然有序，过期点击一定在队首，可用队列头部删除，摊还 O(1)。
3. **两种经典实现**：
   - **队列（时间戳）**：每次 `hit` 入队一个时间戳；`getHits` 时弹出所有 `< timestamp - 299` 的队首，返回队列长度。简单直观，空间 O(命中数)。
   - **环形数组（固定 300 桶）**：用 300 个桶按「秒 mod 300」分桶，存 `(时间戳, 计数)`；遇到新时间戳且过期则清零该桶。空间 O(300)，但需处理「同一秒多次 hit」与「跨周期复用」。
4. **边界**：同一时间戳多次点击、`getHits` 窗口左边界 `timestamp - 299` 的闭区间语义、首条点击后立即查询。

## 解题思路

### 方案 A：队列

- 维护 `queue: number[]` 保存每次点击的时间戳（一个 hit 一个元素）。
- `hit(t)`：`queue.push(t)`。
- `getHits(t)`：`while (queue.length && queue[0] < t - 299) queue.shift()`；返回 `queue.length`。
- 由于时间戳递增，`shift()` 总次数 = 总 hit 次数，摊还 O(1)。

### 方案 B：环形数组（固定大小）

- `times: number[]`（长度 300）与 `counts: number[]`（长度 300）。
- `hit(t)`：`idx = t % 300`；若 `times[idx] !== t`，则 `times[idx] = t; counts[idx] = 0`；`counts[idx]++`。
- `getHits(t)`：遍历 300 个桶，累加 `times[i] >= t - 299` 的 `counts[i]`，返回总和。时间 O(300)。

## 复杂度

- 方案 A：`hit` O(1)，`getHits` 摊还 O(1)；空间 O(命中次数)。
- 方案 B：`hit` O(1)，`getHits` O(300)；空间 O(300) 固定。

## 参考代码（队列）

```ts
class HitCounter {
  private queue: number[] = [];

  hit(timestamp: number): void {
    this.queue.push(timestamp);
  }

  getHits(timestamp: number): number {
    const threshold = timestamp - 299;
    while (this.queue.length && this.queue[0] < threshold) {
      this.queue.shift();
    }
    return this.queue.length;
  }
}
```

## 参考代码（环形数组）

```ts
class HitCounter {
  private times = new Array<number>(300).fill(0);
  private counts = new Array<number>(300).fill(0);

  hit(timestamp: number): void {
    const idx = timestamp % 300;
    if (this.times[idx] !== timestamp) {
      this.times[idx] = timestamp;
      this.counts[idx] = 0;
    }
    this.counts[idx]++;
  }

  getHits(timestamp: number): number {
    let total = 0;
    for (let i = 0; i < 300; i++) {
      if (this.times[i] >= timestamp - 299) {
        total += this.counts[i];
      }
    }
    return total;
  }
}
```

## 追问 / Follow-ups

1. **并发场景**（多线程同时 hit）？→ 加锁或用原子计数；分布式下用 Redis 的 ZSET（score 存时间戳）或时间分桶。
2. **点击量极大、时间跨度极长**？→ 队列会占大量内存，改用环形数组 + 聚合计数，或滚动窗口抽样（近似计数）。
3. 若 `getHits` 也需要 O(1)？→ 环形数组方案查询仍是 O(300)；可再加一个「前缀和」结构，但需处理窗口滑动，通常 300 常数可接受。
