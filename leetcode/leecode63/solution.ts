/**
 * 考点：Array, Dynamic Programming, Matrix
 * 题目：Unique Paths II（不同路径 II）
 * 题目描述：机器人位于 m×n 网格左上角，每次只能向下或向右移动。网格中有障碍物(1)和空位(0)，求到达右下角的不同路径数。
 * 示例：obstacleGrid = [[0,0,0],[0,1,0],[0,0,0]] → 2
 * 思路：动态规划。若当前位置是障碍物，dp[j]=0；否则 dp[j] += dp[j-1]。空间优化为一维数组。
 *       起点/终点是障碍物直接返回 0。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)
 */
function uniquePathsWithObstacles(obstacleGrid: number[][]): number {
    const m = obstacleGrid.length;
    const n = obstacleGrid[0].length;

    if (obstacleGrid[0][0] === 1 || obstacleGrid[m - 1][n - 1] === 1) {
        return 0;
    }

    const dp: number[] = new Array(n).fill(0);
    dp[0] = 1;

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            if (obstacleGrid[i][j] === 1) {
                dp[j] = 0;
            } else if (j > 0) {
                dp[j] += dp[j - 1];
            }
        }
    }

    return dp[n - 1];
}

export { uniquePathsWithObstacles };
