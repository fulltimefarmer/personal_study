# Promise.all — 考点分析与解题思路

## 考点分析

1. **Promise 构造与状态机**：`new Promise((resolve, reject) => {...})`，在内部订阅每个输入 promise，全部成功后 `resolve`，任一失败 `reject`。
2. **结果顺序**：不能用 `push`（那样顺序取决于完成先后），而要用**按下标赋值** `results[i] = value`，并用 `completed` 计数判断是否全部完成。
3. **fail-fast**：任意 promise `reject` 时立即 `reject`，不再等待其余；后续的 `resolve`/`reject` 天然被忽略（Promise 状态不可变）。
4. **普通值包装**：用 `Promise.resolve(p)` 统一处理，保证 `.then` 可用。
5. **空输入**：直接 `resolve([])`（注意别让 `completed === 0 === length` 的边界误判）。

## 解题思路

- 返回 `new Promise((resolve, reject) => ...)`。
- 空数组直接 `resolve([])`。
- 创建 `results = new Array(n)` 与 `completed = 0`。
- `promises.forEach((p, i) => Promise.resolve(p).then(v => { results[i] = v; if (++completed === n) resolve(results); }, reject))`。

## 复杂度

- 时间：O(n)，每个 promise 订阅一次。
- 空间：O(n)，结果数组。

## 参考代码

```ts
function promiseAll<T>(promises: Array<T | PromiseLike<T>>): Promise<T[]> {
  return new Promise((resolve, reject) => {
    const n = promises.length;
    if (n === 0) { resolve([]); return; }

    const results = new Array<T>(n);
    let completed = 0;

    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        value => {
          results[i] = value;
          completed++;
          if (completed === n) resolve(results);
        },
        reason => reject(reason)
      );
    });
  });
}
```

## 追问 / Follow-ups

1. **Promise.allSettled**？→ 不 fail-fast，每个 promise 无论成败都记录 `{status, value/reason}`，全部完成后 resolve。
2. **Promise.race / any**？→ race 返回最先 settle 的结果；any 返回第一个 fulfill（全 reject 时抛 AggregateError）。
3. **顺序执行 promise 数组**（而非并发）？→ 用 `reduce` 串成 `.then` 链，或递归 `helper(index, results)`。
4. **并发限流**（最多 N 个并发）？→ 维护一个「并发池」，用计数器/信号量控制同时进行中的任务数（后端 Node.js 常见）。
