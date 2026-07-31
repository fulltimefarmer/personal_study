/**
 * 考点：Dynamic Programming、Divide and Conquer
 * 题目：Maximum Subarray
 * 题目描述：给你一个整数数组 nums，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。
 *          子数组是数组中的一个连续部分。
 *          示例：输入 nums = [-2,1,-3,4,-1,2,1,-5,4]，输出 6；最大子数组为 [4,-1,2,1]。
 * 思路：第一步：用 curSum 记录以当前元素结尾的最大子数组和，maxSum 记录全局最大值。
 *       第二步：初始化 curSum = nums[0]、maxSum = nums[0]，从 i = 1 开始遍历数组。
 *       第三步：状态转移 curSum = Math.max(nums[i], curSum + nums[i])：
 *              若 curSum 为负数，对后续元素无益，因此从当前元素重新开始累加；
 *              否则将当前元素加入之前的子数组。
 *       第四步：每轮更新 maxSum = Math.max(maxSum, curSum)，保存全局最大值。
 *       第五步：遍历结束返回 maxSum。
 * 算法：动态规划 / Kadane 算法。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
public class Solution {
    public int maxSubArray(int[] nums) {
        int curSum = nums[0];
        int maxSum = nums[0];
        for (int i = 1; i < nums.length; i++) {
            curSum = Math.max(nums[i], curSum + nums[i]);
            maxSum = Math.max(maxSum, curSum);
        }
        return maxSum;
    }
}
