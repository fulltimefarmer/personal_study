# Flatten Array · 展平嵌套数组

- **类型 Type:** 非算法 · JS/TS 手写实现 / Array Method
- **难度 Difficulty:** Easy
- **标签 Topics:** 数组 / 递归 / Array / Recursion
- **苹果频率:** 高频（frontendinterviewhandbook Apple 专区明确「实现 `Array.prototype.flat`」）

## 题干（中文）

不借助原生的 `Array.prototype.flat`，实现一个 `flatten(arr, depth?)` 函数，将嵌套数组展平：

1. 返回一个新数组，包含原数组中所有元素。
2. 若元素是数组且深度未达上限，则递归展平；否则原样保留。
3. `depth` 指定展平的最大深度，**默认为 `1`**（与原生 `flat()` 一致）；`depth = Infinity` 表示完全展平。

## Problem Statement (English)

Implement `flatten(arr, depth?)` without using the native `Array.prototype.flat`:

1. Returns a new array with all elements of the input.
2. Recursively flattens array elements up to the given depth; otherwise keeps them as-is.
3. `depth` is the maximum depth to flatten, **defaulting to `1`** (same as native `flat()`); `Infinity` means fully flatten.

## 示例 / Examples

```ts
flatten([1, 2, [3, 4]]);
// => [1, 2, 3, 4]

flatten([1, [2, [3, [4]]]], 1);
// => [1, 2, [3, [4]]]（只展平一层）

flatten([1, [2, [3, [4]]]], 2);
// => [1, 2, 3, [4]]

flatten([1, [2, [3, [4]]]], Infinity);
// => [1, 2, 3, 4]（完全展平）

flatten([]);
// => []
```

## 约束 / Constraints

- 元素可为任意类型（数字、字符串、数组等），但展平仅针对数组元素
- `depth >= 0`（`depth = 0` 时原样返回）
