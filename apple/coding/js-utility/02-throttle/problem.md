# Throttle · 节流

- **类型 Type:** 非算法 · JS/TS 手写工具函数 / Utility Function
- **难度 Difficulty:** Easy
- **标签 Topics:** 闭包 / 定时器 / 性能优化 / Closure / Timer / Performance
- **苹果频率:** 高频（Apple scroll/resize 场景必问，常与 debounce 成对考察）

## 题干（中文）

实现一个 `throttle(fn, wait)` 函数，返回一个「节流」后的新函数：无论它被调用的多频繁，`fn` 在任意 `wait` 毫秒内**最多执行一次**。

要求：

1. 返回的函数应**保留 `this` 与所有参数**。
2. 建议支持**前置（leading）触发**（第一次调用立即执行），并可选地支持**尾随（trailing）触发**（窗口末尾若仍有调用则补一次）。
3. 不要求实现 `cancel()`（如实现可加分）。

典型场景：监听 `scroll`、`mousemove`、`resize` 等高频事件，降低回调执行频率。

## Problem Statement (English)

Implement a `throttle(fn, wait)` function that returns a throttled version of `fn`: no matter how frequently it is called, `fn` executes **at most once** every `wait` milliseconds.

Requirements:

1. Preserve `this` and all arguments.
2. Support **leading** invocation (first call fires immediately), and optionally a **trailing** invocation (a pending call at the edge of the window fires once at the end).
3. `cancel()` is optional (a bonus).

## 示例 / Examples

```ts
const log = throttle((x: number) => console.log(x), 100);

log(1);   // 立即执行，输出 1
log(2);   // 忽略（仍在 100ms 窗口内）
log(3);   // 忽略
// ... 100ms 后若仍被调用，则再执行一次（尾随）
```

## 约束 / Constraints

- `wait` 为非负整数（毫秒）
- 可忽略传入函数的返回值（`fn` 按返回 `void` 处理）
