/**
 * 考点：Dynamic Programming、Divide and Conquer
 * 题目：Maximum Subarray
 * 题目描述：给你一个整数数组 nums，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。
 *          子数组是数组中的一个连续部分。
 *          示例：输入 nums = [-2,1,-3,4,-1,2,1,-5,4]，输出 6；最大子数组为 [4,-1,2,1]。
 * 思路：第一步：定义 curSum 表示以当前元素 nums[i] 结尾的子数组的最大和；
 *              定义 maxSum 表示全局最大子数组和。
 *       第二步：初始化 curSum = nums[0]、maxSum = nums[0]，从第二个元素开始遍历。
 *       第三步：状态转移：curSum = max(nums[i], curSum + nums[i])。
 *              含义是：要么从当前元素重新开始计算子数组，要么将当前元素加入前面的子数组。
 *       第四步：每轮更新 maxSum = max(maxSum, curSum)，确保 maxSum 始终保存遍历过程中的最大值。
 *       第五步：遍历结束后返回 maxSum。
 * 算法：动态规划 / Kadane 算法。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxSubArray(nums: number[]): number {
    let curSum = nums[0];
    let maxSum = nums[0];
    for (let i = 1; i < nums.length; i++) {
        curSum = Math.max(nums[i], curSum + nums[i]);
        maxSum = Math.max(maxSum, curSum);
    }
    return maxSum;
}
