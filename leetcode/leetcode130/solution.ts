/**
 * 考点：DFS、BFS、并查集、数组、矩阵
 * 题目：Surrounded Regions（被围绕的区域）
 * 题目描述：将矩阵中被 'X' 包围的 'O' 填充为 'X'。边界上的 'O' 及其相连的 'O' 不被填充。
 *   示例：board = [["X","X","X","X"],["X","O","O","X"],["X","X","O","X"],["X","O","X","X"]]
 * 思路：从边界 'O' 开始 DFS，标记所有不被填充的 'O'，最后统一处理。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(m × n)，递归栈
 */

/**
 * Do not return anything, modify board in-place instead.
 */
function solve(board: string[][]): void {
  const m = board.length;
  const n = board[0].length;

  function dfs(i: number, j: number): void {
    if (i < 0 || i >= m || j < 0 || j >= n || board[i][j] !== 'O') {
      return;
    }
    board[i][j] = '#';
    dfs(i - 1, j);
    dfs(i + 1, j);
    dfs(i, j - 1);
    dfs(i, j + 1);
  }

  for (let i = 0; i < m; i++) {
    dfs(i, 0);
    dfs(i, n - 1);
  }
  for (let j = 0; j < n; j++) {
    dfs(0, j);
    dfs(m - 1, j);
  }

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (board[i][j] === 'O') {
        board[i][j] = 'X';
      } else if (board[i][j] === '#') {
        board[i][j] = 'O';
      }
    }
  }
}

export { solve };
