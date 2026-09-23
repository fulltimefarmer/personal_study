# Product of Array Except Self — 考点分析与解题思路

## 考点分析

1. **前缀积 × 后缀积**：`answer[i] = (nums[0]…nums[i-1] 的积) × (nums[i+1]…nums[n-1] 的积)`。分别维护「左侧乘积」与「右侧乘积」。
2. **禁止除法**：除法会因 `0` 的存在而失效（除以 0 非法），且可能溢出/精度问题，因此必须用乘法拆分。
3. **O(1) 额外空间**：用输出数组 `answer` 本身先存「左侧积」，再从右往左用一个变量 `right` 累积「右侧积」乘回去，避免开两个辅助数组。
4. **边界**：数组含 `0`（多个 0 时结果全 0）、含负数、n=2。

## 解题思路（两次遍历，O(1) 额外空间）

1. 初始化 `answer`，先算**左侧积**：
   - `answer[0] = 1`；
   - 从左到右：`answer[i] = answer[i-1] * nums[i-1]`。此时 `answer[i]` 是 `nums[0..i-1]` 的乘积。
2. 再算**右侧积**并乘入：
   - `right = 1`；
   - 从右到左：`answer[i] *= right`，然后 `right *= nums[i]`。
3. 返回 `answer`。

## 复杂度

- 时间：O(n)，两次遍历。
- 空间：O(1)，输出数组不计入额外空间。

## 参考代码

```ts
function productExceptSelf(nums: number[]): number[] {
  const n = nums.length;
  const answer = new Array(n).fill(1);

  // 左侧积：answer[i] = nums[0] * ... * nums[i-1]
  for (let i = 1; i < n; i++) {
    answer[i] = answer[i - 1] * nums[i - 1];
  }

  // 右侧积：从右往左乘入
  let right = 1;
  for (let i = n - 1; i >= 0; i--) {
    answer[i] *= right;
    right *= nums[i];
  }

  return answer;
}
```

## 追问 / Follow-ups

1. 为什么不能用除法？→ 除 0 非法；且可能溢出/精度丢失；约束明确禁止。
2. 如果允许除法怎么做？→ 先算总积，再除以每个元素，但要单独统计 0 的个数（0 个、1 个、多个 0 三种情况）。
3. **前缀和/前缀积**的通用思想还能解哪些题？→ 子数组和等于 K（LeetCode 560，前缀和 + 哈希）、区间和查询（LeetCode 303）、除自身外数组的乘积。
4. 如何证明 O(1) 空间？→ 只用输出数组 + 一个变量，符合「输出不计入额外空间」的惯例。
