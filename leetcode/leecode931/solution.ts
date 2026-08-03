/**
 * 考点：数组, 动态规划, 矩阵
 * 题目：Minimum Falling Path Sum（下降路径最小和）
 * 题目描述：n x n 矩阵，下降路径从第一行任意位置开始，每行可选正下方、左下或右下元素。求下降路径的最小和。
 * 示例：
 *   输入: [[2,1,3],[6,5,4],[7,8,9]] → 输出: 13
 * 思路：DP。dp[i][j]=matrix[i][j]+min(dp[i-1][j-1],dp[i-1][j],dp[i-1][j+1])。最终 min(dp[n-1])。空间优化为 O(n)。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n)
 */
function minFallingPathSum(matrix: number[][]): number {
    const n = matrix.length;
    let prev = [...matrix[0]];

    for (let i = 1; i < n; i++) {
        const curr: number[] = new Array(n).fill(0);
        for (let j = 0; j < n; j++) {
            let minAbove = prev[j];
            if (j > 0) minAbove = Math.min(minAbove, prev[j - 1]);
            if (j < n - 1) minAbove = Math.min(minAbove, prev[j + 1]);
            curr[j] = matrix[i][j] + minAbove;
        }
        prev = curr;
    }

    return Math.min(...prev);
}

export { minFallingPathSum };
