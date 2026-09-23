# Design Hit Counter · 设计点击计数器

- **LeetCode:** 362
- **难度 Difficulty:** Medium
- **标签 Topics:** 设计 / 队列 / 数据流 / Design / Queue / Data Stream
- **苹果频率:** 高频（Verve/候选面经均列为 Apple 高频设计题，数据流 + 时间窗口）

## 题干（中文）

设计一个点击计数器，用它来记录过去 **5 分钟（300 秒）**内的点击次数。

实现 `HitCounter` 类：

- `HitCounter()`：初始化点击计数器。
- `hit(timestamp: number): void`：记录在 `timestamp`（以秒为单位）发生的一次点击。每个 `timestamp` 可能有多次点击。题目保证对 `hit` 的调用是按 `timestamp` **递增（非递减）**顺序进行的。
- `getHits(timestamp: number): number`：返回过去 300 秒内的点击次数，即范围 `[timestamp - 299, timestamp]`（闭区间）内的点击总数。

## Problem Statement (English)

Design a hit counter which counts the number of hits received in the past **5 minutes (300 seconds)**.

Implement the `HitCounter` class:

- `HitCounter()`: initializes the object of the hit counter.
- `hit(timestamp: number)`: records a hit that happened at `timestamp` (in seconds). Several hits may happen at the same timestamp. Calls to `hit` are in **increasing (non-decreasing)** timestamp order.
- `getHits(timestamp: number)`: returns the number of hits in the past 300 seconds, i.e. in the inclusive range `[timestamp - 299, timestamp]`.

## 示例 / Example

```ts
const counter = new HitCounter();
counter.hit(1);      // 1 秒处点击一次
counter.hit(2);      // 2 秒处点击一次
counter.hit(3);      // 3 秒处点击一次
counter.getHits(4);  // 返回 3（时间 [1,2,3] 都在 300 秒窗口内）
counter.hit(300);    // 300 秒处点击一次
counter.getHits(300); // 返回 4（范围 [1,300]）
counter.getHits(301); // 返回 3（范围 [2,301]，1 秒的点击已过期）
```

## 约束 / Constraints

- `1 <= timestamp <= 2 * 10^9`
- 所有对 `hit` 与 `getHits` 的调用都按时间戳**递增顺序**进行（即后续调用的时间戳 ≥ 之前的）
- `hit` 与 `getHits` 至多调用 `300` 次
