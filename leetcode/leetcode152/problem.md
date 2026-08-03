# LeetCode 152. Maximum Product Subarray（乘积最大子数组）

## 考点
数组、动态规划

## 题目描述
给你一个整数数组 `nums`，请你找出数组中乘积最大的非空连续子数组（该子数组中至少包含一个数字），并返回该子数组所对应的乘积。

测试用例的答案是一个**32 位**整数。

**示例 1：**
```
输入：nums = [2,3,-2,4]
输出：6
解释：子数组 [2,3] 有最大乘积 6。
```

**示例 2：**
```
输入：nums = [-2,0,-1]
输出：0
```

**提示：**
- `1 <= nums.length <= 2 * 10^4`
- `-10 <= nums[i] <= 10`
- 子数组的乘积保证在 32 位整数范围内

## 解题思路
**动态规划，同时维护最大值和最小值。**

由于存在负数，最小值乘以负数可能变成最大值，最大值乘以负数可能变成最小值。因此需要同时维护当前结尾的子数组的最大乘积和最小乘积。

**状态定义：**
- `maxDp`：以当前位置结尾的子数组的最大乘积
- `minDp`：以当前位置结尾的子数组的最小乘积

**状态转移：**
对于当前元素 `num`：
- 如果 `num >= 0`：
  - `maxDp = max(maxDp * num, num)`
  - `minDp = min(minDp * num, num)`
- 如果 `num < 0`：最大值和最小值交换后再计算
  - 先将 `maxDp` 和 `minDp` 交换（因为乘以负数后，大的变小，小的变大）
  - `maxDp = max(maxDp * num, num)`
  - `minDp = min(minDp * num, num)`

**实际上可以统一写法：**
```typescript
const candidates = [num, num * maxDp, num * minDp];
maxDp = Math.max(...candidates);
minDp = Math.min(...candidates);
```

**关键点：**
- 同时维护最大和最小值
- 全局最大值记录结果

时间复杂度：O(n)  
空间复杂度：O(1)
