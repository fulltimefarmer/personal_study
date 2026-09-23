# Top K Frequent Elements — 考点分析与解题思路

## 考点分析

1. **计数是第一步**：用 `Map<number, number>` 统计每个元素的频率。
2. **「Top K」的三种解法**：
   - **最小堆（size k）**：维护大小为 k 的最小堆，遍历所有 (值, 频率)，堆满时若新频率大于堆顶则替换。时间 O(n log k)。
   - **桶排序（计数排序思想）**：以「频率」为下标建桶 `buckets[freq] = 元素列表`，频率范围是 `[0, n]`；从高到低收集前 k 个。时间 O(n)，是最优解。
   - **快速选择（Quickselect）**：按频率做部分排序，平均 O(n)。
3. **JS 无内置堆**：要么手写最小堆，要么用桶排序（更简洁、且时间更优）。
4. **边界**：`k == 1`、所有元素相同、频率并列、k 等于不同元素总数。

## 解题思路（桶排序，O(n)）

1. 用 `Map` 统计频率 `freq`。
2. 建桶：`buckets = Array(n + 1).fill(null)`（频率最大为 n）；对每个 `[num, f]`，`buckets[f].push(num)`。
3. 从 `buckets[n]` 向下遍历，收集元素直到凑满 `k` 个。

## 复杂度

- 桶排序：时间 O(n)，空间 O(n)。

## 参考代码（桶排序）

```ts
function topKFrequent(nums: number[], k: number): number[] {
  const freq = new Map<number, number>();
  for (const n of nums) {
    freq.set(n, (freq.get(n) ?? 0) + 1);
  }

  const buckets: number[][] = Array.from({ length: nums.length + 1 }, () => []);
  for (const [num, f] of freq) {
    buckets[f].push(num);
  }

  const result: number[] = [];
  for (let i = buckets.length - 1; i >= 0 && result.length < k; i--) {
    for (const num of buckets[i]) {
      result.push(num);
      if (result.length === k) return result;
    }
  }
  return result;
}
```

## 参考代码（最小堆，size k）

```ts
function topKFrequent(nums: number[], k: number): number[] {
  const freq = new Map<number, number>();
  for (const n of nums) freq.set(n, (freq.get(n) ?? 0) + 1);

  // 最小堆：按频率排序，堆顶是最小频率
  const heap: [number, number][] = []; // [frequency, num]
  const push = (item: [number, number]) => {
    heap.push(item);
    let i = heap.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heap[p][0] <= heap[i][0]) break;
      [heap[p], heap[i]] = [heap[i], heap[p]];
      i = p;
    }
  };
  const pop = () => {
    const top = heap[0];
    heap[0] = heap[heap.length - 1];
    heap.pop();
    let i = 0;
    while (true) {
      const l = i * 2 + 1, r = i * 2 + 2;
      let smallest = i;
      if (l < heap.length && heap[l][0] < heap[smallest][0]) smallest = l;
      if (r < heap.length && heap[r][0] < heap[smallest][0]) smallest = r;
      if (smallest === i) break;
      [heap[i], heap[smallest]] = [heap[smallest], heap[i]];
      i = smallest;
    }
    return top;
  };

  for (const [num, f] of freq) {
    push([f, num]);
    if (heap.length > k) pop();
  }

  return heap.map(([, num]) => num);
}
```

## 追问 / Follow-ups

1. 桶排序 vs 堆 vs 快速选择各有什么取舍？→ 桶排序 O(n) 最简；堆 O(n log k) 适合 n 大 k 小且数据流式；快速选择平均 O(n) 但不稳定。
2. **数据流**（元素持续到达）如何维护 Top K？→ 维持 `Map` 计数 + 最小堆 size k。
3. **字符串/对象**版本的 Top K？→ 键换成字符串，计数方式相同。
4. **Kth Largest Element**（LeetCode 215）也常用堆/快速选择，两者可互相迁移。
