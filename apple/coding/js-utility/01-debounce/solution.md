# Debounce — 考点分析与解题思路

## 考点分析

1. **闭包持有计时器**：防抖的本质是用闭包维护一个 `timer` 变量，跨多次调用共享。每次调用先 `clearTimeout` 旧的、再 `setTimeout` 新的，实现「后调用覆盖前调用」。
2. **`this` 与参数透传**：延迟执行时必须用 `fn.apply(this, args)`（或箭头函数捕获调用时的 `this`/`args`），否则调用者上下文和参数会丢失。
3. **前置 vs 尾随**：`immediate` 控制触发时机。
   - 尾随（默认）：停顿 `wait` 后才执行。
   - 前置：`timer === null`（无待触发）时立即执行，随后设置一个「解锁」计时器，冷却期内不再触发。
4. **`cancel()`**：清除计时器并复位 `timer`，避免计时器残留导致误触发。
5. **常见 Bug**：在 React 中若每次 render 都新建 debounced 函数，闭包里的 `timer` 每次都是新的，防抖失效——需用 `useCallback`/`useMemo` 包裹（面试常见追问）。

## 解题思路

- 定义 `timer: ReturnType<typeof setTimeout> | null = null`。
- 返回 `debounced` 函数：
  - 若 `immediate`：`callNow = timer === null`；清旧计时器；设置解锁计时器（结束后 `timer = null`）；若 `callNow` 立即 `fn.apply(this, args)`。
  - 否则（尾随）：清旧计时器；`timer = setTimeout(() => { timer = null; fn.apply(this, args); }, wait)`。
- `debounced.cancel = () => { clearTimeout(timer); timer = null; }`。

## 复杂度

- 时间：每次调用 O(1)。
- 空间：O(1)（仅一个计时器引用）。

## 参考代码

```ts
type Procedure = (...args: any[]) => void;

function debounce<F extends Procedure>(
  fn: F,
  wait: number,
  immediate = false
) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  const debounced = function (this: unknown, ...args: Parameters<F>) {
    const callNow = immediate && timer === null;
    if (timer) clearTimeout(timer);

    timer = setTimeout(() => {
      timer = null;
      if (!immediate) fn.apply(this, args);
    }, wait);

    if (callNow) fn.apply(this, args);
  } as F & { cancel: () => void };

  debounced.cancel = () => {
    if (timer) clearTimeout(timer);
    timer = null;
  };

  return debounced;
}
```

## 追问 / Follow-ups

1. **debounce 与 throttle 的区别？**→ debounce 等「停止调用」后触发（只关心最终值），throttle 按固定节奏触发（关心过程采样）。搜索/ resize 用 debounce，scroll/鼠标移动用 throttle。
2. **前置 + 尾随都要**（leading + trailing）？→ 加 `maxWait`/标志位控制，Lodash 的完整实现较复杂，面试通常不要求。
3. **React 中如何正确使用？**→ 用 `useCallback(() => debounce(fn, wait), [])` 或 `useMemo` 缓存，并在 `useEffect` 清理阶段调用 `.cancel()`。
4. **如何测试异步防抖？**→ 用假时钟（jest fake timers / sinon）或 `await sleep()`，避免真实等待。
