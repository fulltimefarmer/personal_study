# Promise.all · 实现 Promise.all

- **类型 Type:** 非算法 · JS/TS 手写实现 / Polyfill
- **难度 Difficulty:** Medium
- **标签 Topics:** Promise / 异步 / 并发 / Async / Concurrency / Microtask
- **苹果频率:** 高频（Apple 面经多次考 promise 输出与实现；frontendinterviewhandbook 列「实现 Promise/Promise.all」）

## 题干（中文）

不借助原生的 `Promise.all`，实现一个 `promiseAll(promises)` 函数，其行为与 `Promise.all` 一致：

1. 接收一个可迭代的 promise 列表，返回一个新的 `Promise`。
2. 当**所有** promise 都成功时，用**与输入相同顺序**的结果数组 `resolve`。
3. 若其中**任意一个** promise 失败，立即用该错误 `reject`（fail-fast，不等待其余完成）。
4. 输入为空数组时，`resolve` 空数组 `[]`。
5. 输入中的元素可能是普通值（非 promise），需用 `Promise.resolve` 包装处理。

## Problem Statement (English)

Implement `promiseAll(promises)` without using the native `Promise.all`, with identical semantics:

1. Takes an iterable of promises and returns a new `Promise`.
2. Resolves with an array of results in the **same order as the input** when all promises fulfill.
3. Rejects immediately with the first rejection reason (fail-fast).
4. Resolves to `[]` for an empty input.
5. Non-promise values in the input must be wrapped via `Promise.resolve`.

## 示例 / Examples

```ts
await promiseAll([Promise.resolve(1), Promise.resolve(2)]);
// => [1, 2]

await promiseAll([1, Promise.resolve(2), 3]);
// => [1, 2, 3]（普通值被包装）

await promiseAll([]);
// => []

await promiseAll([
  Promise.resolve(1),
  Promise.reject(new Error("boom")),
  new Promise(r => setTimeout(() => r(3), 1000)),
]).catch(e => e.message);
// => "boom"（立即 reject，不等待 1s 的第三个）
```

## 约束 / Constraints

- 输入为可迭代对象（数组即可）
- 结果数组长度与输入长度一致
- 需要处理「后完成的 promise 先 resolve」时结果仍按输入顺序排列
