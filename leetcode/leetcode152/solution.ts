/**
 * 考点：数组、动态规划
 * 题目：Maximum Product Subarray（乘积最大子数组）
 * 题目描述：求乘积最大的连续子数组。
 *   示例：nums = [2,3,-2,4] → 6（子数组 [2,3]）
 * 思路：动态规划。同时维护以当前位置结尾的最大乘积和最小乘积。
 *   负数会使最大变小、最小变大，所以遇到负数时交换两者。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function maxProduct(nums: number[]): number {
  let maxDp = nums[0];
  let minDp = nums[0];
  let result = nums[0];

  for (let i = 1; i < nums.length; i++) {
    const num = nums[i];
    if (num < 0) {
      [maxDp, minDp] = [minDp, maxDp];
    }
    maxDp = Math.max(num, maxDp * num);
    minDp = Math.min(num, minDp * num);
    result = Math.max(result, maxDp);
  }

  return result;
}

export { maxProduct };
