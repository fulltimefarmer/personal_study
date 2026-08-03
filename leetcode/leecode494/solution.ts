/**
 * 考点：数组, 动态规划, 回溯
 * 题目：Target Sum（目标和）
 * 题目描述：给定非负整数数组 nums 和整数 target。在每个数前添加 '+' 或 '-'，求运算结果等于 target 的不同表达式数目。
 * 示例：
 *   输入: nums=[1,1,1,1,1], target=3 → 输出: 5
 * 思路：转化为 0-1 背包。设 P 为加'+'的数字和，则 P = (target+sum)/2。问题变成选若干个数和为 P 的方案数。dp[j] += dp[j-num]。
 * 时间复杂度：O(n * P)
 * 空间复杂度：O(P)
 */
function findTargetSumWays(nums: number[], target: number): number {
    const sum = nums.reduce((a, b) => a + b, 0);

    if (Math.abs(target) > sum || (target + sum) % 2 !== 0) {
        return 0;
    }

    const P = (target + sum) / 2;
    const dp: number[] = new Array(P + 1).fill(0);
    dp[0] = 1;

    for (const num of nums) {
        for (let j = P; j >= num; j--) {
            dp[j] += dp[j - num];
        }
    }

    return dp[P];
}

export { findTargetSumWays };
