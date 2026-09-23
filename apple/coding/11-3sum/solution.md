# 3Sum — 考点分析与解题思路

## 考点分析

1. **降维 + 双指针**：三数之和无法直接用两数之和的哈希法（去重复杂）。标准做法是「先排序，固定一个数，转成在剩余部分求两数之和」，用首尾双指针线性扫描。
2. **排序是关键前提**：排序后可用「`sum` 偏小则左指针右移、偏大则右指针左移」的单调性剪枝，把内层从 O(n²) 降到 O(n)。
3. **去重是本题难点**（Apple 面试尤其看重）：
   - 固定数去重：`if (i > 0 && nums[i] === nums[i - 1]) continue;`
   - 指针去重：找到一组解后，跳过相邻相同元素再移动指针。
4. **剪枝**：固定数 `nums[i] > 0` 时，因为后面都更大，三数之和必大于 0，可提前 `break`。

## 解题思路

- 对 `nums` 升序排序。
- 遍历 `i`（固定第一个数），跳过重复值。
- 设 `left = i + 1`、`right = n - 1`，求 `sum = nums[i] + nums[left] + nums[right]`：
  - `sum === 0`：记录结果，`left++`/`right--`，并跳过重复元素；
  - `sum < 0`：`left++`；
  - `sum > 0`：`right--`。

## 复杂度

- 时间：O(n²)，排序 O(n log n) + 外层 n × 内层双指针 n。
- 空间：O(log n)（排序栈；若计入结果集为 O(k)，k 为三元组个数）。

## 参考代码

```ts
function threeSum(nums: number[]): number[][] {
  nums.sort((a, b) => a - b);
  const res: number[][] = [];
  const n = nums.length;

  for (let i = 0; i < n - 2; i++) {
    if (nums[i] > 0) break;                        // 后面都更大，无解
    if (i > 0 && nums[i] === nums[i - 1]) continue; // 固定数去重

    let left = i + 1;
    let right = n - 1;
    while (left < right) {
      const sum = nums[i] + nums[left] + nums[right];
      if (sum === 0) {
        res.push([nums[i], nums[left], nums[right]]);
        while (left < right && nums[left] === nums[left + 1]) left++;   // 左去重
        while (left < right && nums[right] === nums[right - 1]) right--; // 右去重
        left++;
        right--;
      } else if (sum < 0) {
        left++;
      } else {
        right--;
      }
    }
  }
  return res;
}
```

## 追问 / Follow-ups

1. **3Sum Closest**（LeetCode 16）：求最接近 target 的三数之和 → 相同框架，维护最小差值。
2. **4Sum**（LeetCode 18）：固定两层 + 双指针，复杂度 O(n³)，同样注意去重。
3. 为什么不用哈希表？→ 去重麻烦、空间更高；但若要求不排序，可用「两数之和哈希 + Set 去重三元组」，需额外处理重复。
