/**
 * 考点：Array, Divide and Conquer, Dynamic Programming
 * 题目：Maximum Subarray（最大子数组和）
 * 题目描述：给定整数数组 nums，求具有最大和的连续子数组，返回最大和。
 * 示例：nums = [-2,1,-3,4,-1,2,1,-5,4] → 6（子数组 [4,-1,2,1]）
 * 思路：Kadane 算法。dp[i] = max(nums[i], dp[i-1] + nums[i])，空间优化为 O(1)。
 *       遍历时维护 currentSum（以当前元素结尾的最大和）和 maxSum（全局最大和）。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxSubArray(nums: number[]): number {
    let currentSum = nums[0];
    let maxSum = nums[0];

    for (let i = 1; i < nums.length; i++) {
        currentSum = Math.max(nums[i], currentSum + nums[i]);
        maxSum = Math.max(maxSum, currentSum);
    }

    return maxSum;
}

export { maxSubArray };
