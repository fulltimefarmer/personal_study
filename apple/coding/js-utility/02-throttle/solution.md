# Throttle — 考点分析与解题思路

## 考点分析

1. **固定节奏触发**：与防抖不同，节流保证在任意 `wait` 毫秒内**最多执行一次**，无论调用多频繁，`fn` 都以稳定节奏触发。
2. **两种实现**：
   - **时间戳法（前置 leading）**：记录上次执行时间 `last`，`now - last >= wait` 才执行并更新 `last`。实现最简，但最后一次「落在窗口末尾的调用」不会触发（无尾随）。
   - **组合法（leading + trailing）**：时间戳立即执行 + 计时器补尾随，能捕获窗口末尾的最后一次调用，最接近 Lodash 的行为。
3. **`this` 与参数透传**：同 debounce，需 `fn.apply(this, args)`。
4. **典型场景**：scroll 监听、鼠标移动、resize（需要稳定采样率，而非等用户停下）。

## 解题思路

### 方案 A：时间戳（前置 leading，推荐先写）

- 维护 `last = 0`。
- 每次调用：`now = Date.now()`；若 `now - last >= wait`，则 `last = now` 并 `fn.apply(this, args)`；否则忽略。

### 方案 B：前置 + 尾随（进阶）

- 维护 `last` 与 `timer`。
- `remaining = wait - (now - last)`。
  - `remaining <= 0`：清尾随计时器，`last = now`，立即执行。
  - 否则若无尾随计时器：设 `setTimeout` 在 `remaining` 后触发（补尾随，执行最后一次调用）。

## 复杂度

- 时间：每次调用 O(1)。
- 空间：O(1)。

## 参考代码（前置 leading，时间戳）

```ts
type Procedure = (...args: any[]) => void;

function throttle<F extends Procedure>(fn: F, wait: number) {
  let last = 0;

  return function (this: unknown, ...args: Parameters<F>) {
    const now = Date.now();
    if (now - last >= wait) {
      last = now;
      fn.apply(this, args);
    }
  };
}
```

## 参考代码（前置 + 尾随）

```ts
function throttle<F extends Procedure>(fn: F, wait: number) {
  let last = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  return function (this: unknown, ...args: Parameters<F>) {
    const now = Date.now();
    const remaining = wait - (now - last);

    if (remaining <= 0) {
      if (timer) { clearTimeout(timer); timer = null; }
      last = now;
      fn.apply(this, args);
    } else if (!timer) {
      timer = setTimeout(() => {
        timer = null;
        last = Date.now();
        fn.apply(this, args);
      }, remaining);
    }
  };
}
```

## 追问 / Follow-ups

1. **要不要尾随（trailing）？**→ 时间戳法不补尾随，最后一次调用若落在窗口内会丢失；组合法能补。需和面试官确认需求。
2. **节流 vs 防抖**怎么选？→ 需要「连续过程采样」（scroll/mousemove）用 throttle；只关心「最终结果」（搜索/保存）用 debounce。
3. **节流用于无限滚动 + 去重**？→ 常见组合题：throttle 触发 `fetch`，用 `Set` 按 id 去重已加载项，配合 `IntersectionObserver`。
