# Promise Pool — 考点分析与解题思路

## 考点分析

1. **并发限流（信号量思想）**：核心是「共享的游标 + 固定数量的 worker」。每个 worker 不断从共享游标取下一个任务执行，直到任务取完。worker 数 = `min(limit, n)`，天然把在途任务数压在 `limit` 内。
2. **结果顺序**：用 `results[i] = value` 按下标写入，而非 `push`，避免「完成顺序」污染「输入顺序」。
3. **错误传播**：任一 `fn` reject 时，`Promise.all(workers)` 立即 reject（其余 worker 继续跑但结果被丢弃）。
4. **边界**：空数组直接返回 `[]`；`limit >= n` 退化为 `Promise.all`。

## 解题思路（worker 模型）

- `results = new Array(n)`，`next = 0`（共享游标）。
- 定义 `worker()`：循环取 `i = next++`，若 `i >= n` 返回；否则 `results[i] = await fn(items[i], i)`。
- 启动 `min(limit, n)` 个 worker，`await Promise.all(workers)`，返回 `results`。

## 复杂度

- 时间：O(n)（总任务数不变，并发只影响墙钟时间）。
- 空间：O(n)（结果数组）+ O(limit)（同时在途任务）。

## 参考代码

```ts
async function mapConcurrent<T, R>(
  items: T[],
  limit: number,
  fn: (item: T, index: number) => Promise<R>
): Promise<R[]> {
  const n = items.length;
  const results = new Array<R>(n);
  let next = 0;

  async function worker() {
    while (true) {
      const i = next++;
      if (i >= n) return;
      results[i] = await fn(items[i], i);
    }
  }

  const workers = Array.from(
    { length: Math.min(limit, n) },
    () => worker()
  );
  await Promise.all(workers);
  return results;
}
```

## 追问 / Follow-ups

1. **失败后是否取消在途任务？**→ 上述实现不取消，只是结果被丢弃；如需取消，可引入 `AbortController` 或「一旦失败立即停止分配新任务」的标志位。
2. **动态任务流**（生产者持续产生任务）？→ 用队列 + 信号量（`acquire`/`release`），或借助 `p-limit` 这类库。
3. **如何确定合适的 `limit`？**→ 依据下游 QPS 限制、连接池大小、机器核数；通常通过压测得到拐点。
4. **与 rate limiter 的区别？**→ 并发限流控制「同时在途数量」，rate limiter 控制「单位时间请求速率」，二者常配合使用。
