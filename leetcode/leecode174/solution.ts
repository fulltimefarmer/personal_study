/**
 * 考点：数组、动态规划、矩阵
 * 题目：Dungeon Game（地下城游戏）
 * 题目描述：骑士从左上角出发救右下角的公主，每个格子有生命增减值。求骑士能成功救公主的最小初始生命值。
 * 示例：dungeon=[[-2,-3,3],[-5,-10,1],[10,30,-5]] 输出 7
 * 思路：反向 DP，dp[i][j]=max(1, min(dp[i+1][j], dp[i][j+1]) - dungeon[i][j])，从右下向左上递推。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n) 优化为一维数组
 */
function calculateMinimumHP(dungeon: number[][]): number {
    const m = dungeon.length;
    const n = dungeon[0].length;
    const dp: number[] = new Array(n + 1).fill(Infinity);
    dp[n - 1] = 1;

    for (let i = m - 1; i >= 0; i--) {
        for (let j = n - 1; j >= 0; j--) {
            dp[j] = Math.max(1, Math.min(dp[j], dp[j + 1]) - dungeon[i][j]);
        }
    }

    return dp[0];
}
export { calculateMinimumHP };
