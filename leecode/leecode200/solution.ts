/**
 * 考点：Array, DFS, BFS, Union Find
 * 题目：Number of Islands
 * 题目描述：
 * 给你一个由 '1'（陆地）和 '0'（水）组成的二维网格（二维字符数组），请你计算网格中岛屿的数量。
 * 岛屿总是被水包围，并且每座岛屿只能由水平方向和/或竖直方向上相邻的陆地连接形成。
 * 此外，你可以假设该网格的四条边均被水包围。
 *
 * 示例 1：
 * 输入：grid = [
 *   ["1","1","1","1","0"],
 *   ["1","1","0","1","0"],
 *   ["1","1","0","0","0"],
 *   ["0","0","0","0","0"]
 * ]
 * 输出：1
 *
 * 示例 2：
 * 输入：grid = [
 *   ["1","1","0","0","0"],
 *   ["1","1","0","0","0"],
 *   ["0","0","1","0","0"],
 *   ["0","0","0","1","1"]
 * ]
 * 输出：3
 *
 * 提示：
 * - m == grid.length
 * - n == grid[i].length
 * - 1 <= m, n <= 300
 * - grid[i][j] 的值为 '0' 或 '1'
 *
 * 思路：
 * 1. 遍历二维网格中的每一个格子。
 * 2. 当遇到值为 '1' 的格子时，说明发现一座新岛屿，计数器 count 加 1。
 * 3. 启动深度优先搜索（DFS），将当前格子及其上、下、左、右相邻的所有 '1' 都标记为 '0'，表示该岛屿已被访问。
 * 4. 继续遍历剩余格子，重复步骤 2 和 3，直到所有格子都被处理完毕。
 * 5. 返回 count，即为网格中岛屿的总数。
 * 数据结构/算法：深度优先搜索（DFS）；二维网格原地修改。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)，递归栈最坏情况
 */
function numIslands(grid: string[][]): number {
    if (!grid.length || !grid[0].length) return 0;
    let count = 0;
    const rows = grid.length;
    const cols = grid[0].length;

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (grid[r][c] === "1") {
                count++;
                dfs(r, c);
            }
        }
    }
    return count;

    function dfs(r: number, c: number): void {
        if (r < 0 || c < 0 || r >= rows || c >= cols || grid[r][c] !== "1") return;
        grid[r][c] = "0";
        dfs(r + 1, c);
        dfs(r - 1, c);
        dfs(r, c + 1);
        dfs(r, c - 1);
    }
}
