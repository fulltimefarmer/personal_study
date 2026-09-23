# Flatten Array — 考点分析与解题思路

## 考点分析

1. **递归 + 深度控制**：`flatten(arr, depth)` 中，遇到数组且 `depth > 0` 时递归 `flatten(item, depth - 1)`，否则原样 push。`depth` 每次递归减一，天然实现「最多展平 depth 层」。
2. **`depth = 0` 与 `Infinity` 边界**：`depth = 0` 时不展平（直接返回浅拷贝）；`Infinity` 表示无限递归直至没有数组（`Infinity - 1` 仍为 `Infinity`，判 `depth > 0` 恒真）。
3. **不修改原数组**：返回全新数组，通过 `push`/展开运算符构建。
4. **实现方式对比**：
   - 递归版：简洁，但嵌套极深可能栈溢出。
   - 迭代版（栈/队列 + 显式深度）：可避免递归栈深度问题，但代码稍复杂。

## 解题思路

### 方案 A：递归（推荐）

- 遍历 `arr`：
  - 若 `Array.isArray(item) && depth > 0`：`result.push(...flatten(item, depth - 1))`。
  - 否则 `result.push(item)`。

### 方案 B：`reduce`

- `arr.reduce((acc, item) => acc.concat(Array.isArray(item) && depth > 0 ? flatten(item, depth - 1) : item), [])`。

### 方案 C：迭代（栈 + 显式深度）

- 用栈存 `(元素, 剩余深度)`，遇到数组且深度 > 0 时把其子元素压栈（深度减一），否则进结果。可处理极深嵌套。

## 复杂度

- 时间：O(N)，N 为所有元素总数（含嵌套）。
- 空间：O(N)（结果数组）+ 递归深度 O(D)。

## 参考代码（递归）

```ts
function flatten(arr: any[], depth = 1): any[] {
  const result: any[] = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      result.push(...flatten(item, depth - 1));
    } else {
      result.push(item);
    }
  }
  return result;
}
```

## 参考代码（迭代，避免深递归）

```ts
function flatten(arr: any[], depth = 1): any[] {
  const result: any[] = [];
  const stack: Array<[any, number]> = arr.map(item => [item, depth]);

  while (stack.length) {
    const [item, d] = stack.pop()!;
    if (Array.isArray(item) && d > 0) {
      for (const sub of item) stack.push([sub, d - 1]);
    } else {
      result.push(item);
    }
  }
  return result.reverse();
}
```

## 追问 / Follow-ups

1. **`depth` 为 `Infinity` 时为什么不用特殊处理？**→ `Infinity - 1 === Infinity`，`depth > 0` 恒为真，自然完全展平。
2. **超深嵌套导致栈溢出？**→ 改用迭代版（显式栈），或对递归版做尾递归/循环改写。
3. **展开运算符 `...flatten(...)` 的性能？**→ 结果较大时可改用 `result.push.apply` 或循环 push，避免 `...` 在极长数组上的参数上限。
4. **其他 Array 方法**（`map`/`reduce`/`filter`）手写？→ 注意稀疏数组（empty slot）、`thisArg` 透传等边界，Apple 也常考。
