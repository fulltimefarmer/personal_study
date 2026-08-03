/**
 * 考点：数组、动态规划（排列背包）
 * 题目：Combination Sum IV（组合总和IV）
 * 题目描述：给定不同整数数组和目标值，求排列数（顺序不同视为不同组合）
 * 思路：DP 排列背包。外层遍历 target，内层遍历 nums。
 *       dp[i] += dp[i - num]（i 从 num 到 target）
 *       注意区别：组合背包外层是物品，排列背包外层是容量。
 * 时间复杂度：O(target × n)
 * 空间复杂度：O(target)
 */
function combinationSum4(nums: number[], target: number): number {
    const dp = new Array(target + 1).fill(0);
    dp[0] = 1;

    for (let i = 1; i <= target; i++) {
        for (const num of nums) {
            if (num <= i) {
                dp[i] += dp[i - num];
            }
        }
    }

    return dp[target];
}

export { combinationSum4 };
