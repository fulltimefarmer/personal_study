# Debounce · 防抖

- **类型 Type:** 非算法 · JS/TS 手写工具函数 / Utility Function
- **难度 Difficulty:** Easy
- **标签 Topics:** 闭包 / 定时器 / 事件循环 / Closure / Timer / Event Loop
- **苹果频率:** 高频（Apple 面经多次要求「实现 debounced 搜索」，interviewkickstart 与 frontendinterviewhandbook 均列为 Apple 必考）

## 题干（中文）

实现一个 `debounce(fn, wait, immediate?)` 函数，返回一个「防抖」后的新函数：当连续多次调用它时，只有在上一次调用之后**停顿了 `wait` 毫秒**才真正执行一次 `fn`。

要求：

1. 返回的函数应**保留 `this` 与所有参数**，并在延迟结束后把它们传给 `fn`。
2. 支持 `immediate` 选项：为 `true` 时采用**前置（leading）**触发——第一次调用立即执行，随后在冷却期内忽略后续调用。
3. 返回的函数需附带 `.cancel()` 方法，用于取消防抖计时器（取消后不再触发）。

典型场景：搜索框输入联想（用户停止输入后才发请求）、窗口 resize、表单自动保存。

## Problem Statement (English)

Implement a `debounce(fn, wait, immediate?)` function that returns a debounced version of `fn`: when called repeatedly, it invokes `fn` only after `wait` milliseconds have elapsed since the last call.

Requirements:

1. Preserve `this` and all arguments, passing them to `fn` when it eventually fires.
2. Support an `immediate` option: when `true`, trigger on the **leading** edge (first call fires immediately, subsequent calls within the cooldown are ignored).
3. The returned function should expose a `.cancel()` method to cancel the pending timer.

## 示例 / Examples

```ts
// 尾随（默认）：连续点击，只有停顿 300ms 后才执行最后一次
const save = debounce(() => console.log("saved"), 300);
save(); save(); save(); // 300ms 后输出一次 "saved"

// 前置：第一次点击立即执行，冷却期内忽略后续点击
const onClick = debounce(() => console.log("clicked"), 300, true);
onClick(); onClick(); // 立即输出一次 "clicked"

// 取消：在触发前取消计时器
const fn = debounce(() => console.log("never"), 300);
fn();
fn.cancel(); // 不再有任何输出
```

## 约束 / Constraints

- `wait` 为非负整数（毫秒）
- 可忽略传入函数的返回值（`fn` 按返回 `void` 处理）
