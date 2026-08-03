/**
 * 考点：DFS, BFS, Union Find, Array, Matrix
 * 题目：Surrounded Regions（被围绕的区域）
 * 题目描述：捕获被围绕的区域，边界上的 'O' 及与其相连的 'O' 不被填充。
 * 示例：board = [["X","X","X","X"],["X","O","O","X"],["X","X","O","X"],["X","O","X","X"]]
 * 输出：[["X","X","X","X"],["X","X","X","X"],["X","X","X","X"],["X","O","X","X"]]
 * 思路：从边界 'O' DFS 标记为 '#'，然后遍历矩阵，'O'→'X'，'#'→'O'。
 * 时间复杂度：O(m*n)
 * 空间复杂度：O(m*n)
 */
function solve(board: string[][]): void {
    const m = board.length;
    const n = board[0].length;

    function dfs(i: number, j: number): void {
        if (i < 0 || i >= m || j < 0 || j >= n || board[i][j] !== 'O') return;
        board[i][j] = '#';
        dfs(i + 1, j);
        dfs(i - 1, j);
        dfs(i, j + 1);
        dfs(i, j - 1);
    }

    for (let i = 0; i < m; i++) {
        if (board[i][0] === 'O') dfs(i, 0);
        if (board[i][n - 1] === 'O') dfs(i, n - 1);
    }
    for (let j = 0; j < n; j++) {
        if (board[0][j] === 'O') dfs(0, j);
        if (board[m - 1][j] === 'O') dfs(m - 1, j);
    }

    for (let i = 0; i < m; i++) {
        for (let j = 0; j < n; j++) {
            if (board[i][j] === 'O') board[i][j] = 'X';
            else if (board[i][j] === '#') board[i][j] = 'O';
        }
    }
}

export { solve };
