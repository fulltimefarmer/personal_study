# Promise Pool · 并发任务池（并发限流）

- **类型 Type:** 非算法 · 后端 / 并发控制 / Backend / Concurrency
- **难度 Difficulty:** Medium
- **标签 Topics:** 异步 / 并发 / 信号量 / Async / Concurrency / Semaphore
- **苹果频率:** 中高频（后端 Node.js 处理批量 API/DB 调用必问，Apple 后端面经多次出现「限流/并发」主题）

## 题干（中文）

实现一个 `mapConcurrent(items, limit, fn)` 函数，对数组 `items` 中的每个元素异步调用 `fn(item, index)`，返回与输入顺序一致的结果数组，但**同时最多只有 `limit` 个任务在运行**。

典型场景：批量调用上游 API / 批量写数据库时，若不限制并发数，会打爆下游或触发限流；需要「并发池」把同时在途的请求数控制在 `limit` 以内。

要求：

1. 结果数组顺序与 `items` 一致（即使后提交的任务先完成）。
2. 任意时刻在途任务数 `<= limit`。
3. 任一任务失败时整体 reject（不等待其余任务）。

## Problem Statement (English)

Implement `mapConcurrent(items, limit, fn)` that asynchronously maps `fn(item, index)` over `items`, returning a results array in input order while running **at most `limit` tasks concurrently**.

Use case: batching upstream API calls or DB writes — without a concurrency cap you can overwhelm downstream services; a "promise pool" keeps in-flight requests bounded by `limit`.

Requirements:

1. Result order matches `items` (even if later tasks finish first).
2. At most `limit` tasks in-flight at any time.
3. Reject the whole result if any task fails (without waiting for the rest).

## 示例 / Examples

```ts
const items = [1, 2, 3, 4, 5];
const fn = async (x: number) => {
  await sleep(100 - x * 10);      // 后提交的任务反而更快
  return x * 2;
};

await mapConcurrent(items, 2, fn);
// => [2, 4, 6, 8, 10]（顺序与输入一致，而非完成顺序）
```

## 约束 / Constraints

- `items.length >= 0`
- `limit >= 1`（`limit >= items.length` 时等价于 `Promise.all`）
- `fn` 返回 `Promise<R>`
