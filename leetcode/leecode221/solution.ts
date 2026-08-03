/**
 * 考点：数组、动态规划、矩阵
 * 题目：Maximal Square（最大正方形）
 * 题目描述：在 '0'/'1' 矩阵中找只含 '1' 的最大正方形面积。
 * 示例：matrix=[["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]] 输出 4
 * 思路：DP，dp[i][j]=min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])+1（当 matrix[i][j]=='1'）。一维优化。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)
 */
function maximalSquare(matrix: string[][]): number {
    const m = matrix.length;
    const n = matrix[0].length;
    const dp: number[] = new Array(n + 1).fill(0);
    let maxSide = 0;
    let prev = 0;

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            const temp = dp[j + 1];
            if (matrix[i][j] === '1') {
                dp[j + 1] = Math.min(dp[j], dp[j + 1], prev) + 1;
                maxSide = Math.max(maxSide, dp[j + 1]);
            } else {
                dp[j + 1] = 0;
            }
            prev = temp;
        }
    }

    return maxSide * maxSide;
}
export { maximalSquare };
