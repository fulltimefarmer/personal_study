# Two Sum — 考点分析与解题思路

## 考点分析

1. **哈希表「空间换时间」**：暴力双重循环 O(n²) 会超时。核心洞察：遍历时，对当前元素 `x`，只需要知道「前面是否出现过 `target - x`」，用哈希表存 `值 → 下标`，把查找降为 O(1)。
2. **一次遍历**：边遍历边查边存，天然避免「重复使用同一元素」——因为当前元素尚未入表，只会匹配到之前的下标。
3. **边界**：重复元素（`[3,3]` 目标 6）、负数、元素为 0、target 可能为 0 或负数。返回下标而非值。
4. 高频「热身题」，Apple 常用来考察基础与沟通，务必快速、干净地写出来并讲清复杂度。

## 解题思路

- 维护 `Map<number, number>`，键为数值，值为下标。
- 遍历数组，对每个 `nums[i]`：
  - 计算 `complement = target - nums[i]`。
  - 若 `complement` 在 Map 中，返回 `[map.get(complement), i]`。
  - 否则把 `(nums[i], i)` 存入 Map。
- 返回 `[]` 兜底（题目保证有解）。

## 复杂度

- 时间：O(n)，一次遍历。
- 空间：O(n)，哈希表最坏存 n 个元素。

## 参考代码

```ts
function twoSum(nums: number[], target: number): number[] {
  const seen = new Map<number, number>();

  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (seen.has(complement)) {
      return [seen.get(complement)!, i];
    }
    seen.set(nums[i], i);
  }

  return []; // 题目保证有解，这里仅为类型兜底
}
```

## 追问 / Follow-ups

1. **返回所有不重复的配对**（而非仅一对）？→ 继续遍历，跳过已使用的下标或用 `Set` 去重。
2. **数组已排序**如何优化空间到 O(1)？→ 双指针相向移动（这是「有序数组 Two Sum」或 `3Sum` 的前置技巧）。
3. **3Sum / 4Sum** 如何扩展？→ 排序 + 固定外层 + 内层双指针，注意去重。
4. 若数字极大、`nums[i] + nums[j]` 可能溢出？→ 在 JS 中 `number` 为双精度浮点，`-10^9` 量级不会超出安全整数，但可用 `target - nums[i]` 的方式避免直接求和判断。
