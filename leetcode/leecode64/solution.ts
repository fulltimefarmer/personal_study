/**
 * 考点：Array, Dynamic Programming, Matrix
 * 题目：Minimum Path Sum（最小路径和）
 * 题目描述：给定 m×n 非负整数网格，每次只能向下或向右移动，求从左上角到右下角的最小路径和。
 * 示例：grid = [[1,3,1],[1,5,1],[4,2,1]] → 7
 * 思路：动态规划，原地修改 grid。dp[i][j] = grid[i][j] + min(上方, 左方)。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(1)
 */
function minPathSum(grid: number[][]): number {
    const m = grid.length;
    const n = grid[0].length;

    for (let j = 1; j < n; j++) {
        grid[0][j] += grid[0][j - 1];
    }

    for (let i = 1; i < m; i++) {
        grid[i][0] += grid[i - 1][0];
    }

    for (let i = 1; i < m; i++) {
        for (let j = 1; j < n; j++) {
            grid[i][j] += Math.min(grid[i - 1][j], grid[i][j - 1]);
        }
    }

    return grid[m - 1][n - 1];
}

export { minPathSum };
