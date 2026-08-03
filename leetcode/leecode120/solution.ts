/**
 * 考点：Array, Dynamic Programming
 * 题目：Triangle（三角形最小路径和）
 * 题目描述：给定三角形，找出自顶向下的最小路径和。每一步只能移动到下一行相邻结点（下标相同或 +1）。
 * 示例：triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]，输出 11（2+3+5+1）
 * 思路：自底向上 DP，dp[j] = triangle[i][j] + min(dp[j], dp[j+1])，空间 O(n)。
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(n)
 */
function minimumTotal(triangle: number[][]): number {
    const n = triangle.length;
    const dp: number[] = [...triangle[n - 1]];

    for (let i = n - 2; i >= 0; i--) {
        for (let j = 0; j <= i; j++) {
            dp[j] = triangle[i][j] + Math.min(dp[j], dp[j + 1]);
        }
    }

    return dp[0];
}

export { minimumTotal };
