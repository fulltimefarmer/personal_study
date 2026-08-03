/**
 * 考点：Array, String, Backtracking, Matrix, DFS
 * 题目：Word Search（单词搜索）
 * 题目描述：给定 m×n 字符网格 board 和单词 word，判断单词是否存在于网格中。
 *       字母需按相邻单元格顺序连接，同一单元格不可重复使用。
 * 示例：board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED" → true
 * 思路：DFS 回溯。从每个格子出发搜索，标记已访问（原地字符替换），四个方向递归，回溯恢复。
 * 时间复杂度：O(m × n × 4^L)
 * 空间复杂度：O(L)（递归深度）
 */
function exist(board: string[][], word: string): boolean {
    const m = board.length;
    const n = board[0].length;

    function dfs(i: number, j: number, index: number): boolean {
        if (index === word.length) return true;
        if (i < 0 || i >= m || j < 0 || j >= n || board[i][j] !== word[index]) return false;

        const temp = board[i][j];
        board[i][j] = '#';

        const found =
            dfs(i + 1, j, index + 1) ||
            dfs(i - 1, j, index + 1) ||
            dfs(i, j + 1, index + 1) ||
            dfs(i, j - 1, index + 1);

        board[i][j] = temp;
        return found;
    }

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            if (dfs(i, j, 0)) return true;
        }
    }

    return false;
}

export { exist };
