/**
 * 考点：Math, Dynamic Programming, Combinatorics
 * 题目：Unique Paths（不同路径）
 * 题目描述：机器人位于 m×n 网格左上角，每次只能向下或向右移动，求到达右下角的不同路径数。
 * 示例：m = 3, n = 7 → 28
 * 示例：m = 3, n = 2 → 3
 * 思路：动态规划。dp[i][j] = dp[i-1][j] + dp[i][j-1]，空间优化为一维数组。
 *       也可用组合数学：C(m+n-2, m-1)。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)
 */
function uniquePaths(m: number, n: number): number {
    const dp: number[] = new Array(n).fill(1);

    for (let i = 1; i < m; i++) {
        for (let j = 1; j < n; j++) {
            dp[j] += dp[j - 1];
        }
    }

    return dp[n - 1];
}

export { uniquePaths };
