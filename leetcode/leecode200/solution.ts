/**
 * 考点：DFS、BFS、并查集、数组、矩阵
 * 题目：Number of Islands（岛屿数量）
 * 题目描述：二维网格中 '1' 为陆地，'0' 为水，相邻陆地（水平/竖直）组成岛屿。计算岛屿数量。
 * 示例：grid=[["1","1","0"],["1","0","0"],["0","0","1"]] 输出 2（实际示例看图）
 * 思路：遍历网格，遇到 '1' 计数+1，DFS 将相连陆地全部标记为 '0'。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(m × n)（递归栈）
 */
function numIslands(grid: string[][]): number {
    const m = grid.length;
    const n = grid[0].length;
    let count = 0;

    const dfs = (i: number, j: number): void => {
        if (i < 0 || i >= m || j < 0 || j >= n || grid[i][j] === '0') return;
        grid[i][j] = '0';
        dfs(i - 1, j);
        dfs(i + 1, j);
        dfs(i, j - 1);
        dfs(i, j + 1);
    };

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            if (grid[i][j] === '1') {
                count++;
                dfs(i, j);
            }
        }
    }

    return count;
}
export { numIslands };
