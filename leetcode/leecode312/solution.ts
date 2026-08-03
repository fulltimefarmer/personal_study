/**
 * 考点：数组、动态规划（区间DP）
 * 题目：Burst Balloons（戳气球）
 * 题目描述：戳气球得分等于相邻三个气球数字乘积，求最大分数
 * 思路：区间 DP。反过来想，考虑开区间 (i,j) 中最后一个戳的气球 k。
 *       dp[i][j] = max(dp[i][k] + dp[k][j] + nums[i]*nums[k]*nums[j])
 * 时间复杂度：O(n³)
 * 空间复杂度：O(n²)
 */
function maxCoins(nums: number[]): number {
    const n = nums.length;
    const arr = [1, ...nums, 1];
    const dp: number[][] = Array.from({ length: n + 2 }, () => new Array(n + 2).fill(0));

    for (let len = 2; len <= n + 1; len++) {
        for (let i = 0; i + len <= n + 1; i++) {
            const j = i + len;
            for (let k = i + 1; k < j; k++) {
                dp[i][j] = Math.max(
                    dp[i][j],
                    dp[i][k] + dp[k][j] + arr[i] * arr[k] * arr[j]
                );
            }
        }
    }

    return dp[0][n + 1];
}

export { maxCoins };
