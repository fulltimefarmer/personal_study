"""
考点：DFS, BFS, Union Find, Array, Matrix
题目：Surrounded Regions（被围绕的区域）
题目描述：捕获被围绕的区域，边界上的 'O' 及与其相连的 'O' 不被填充。
示例：board = [["X","X","X","X"],["X","O","O","X"],["X","X","O","X"],["X","O","X","X"]]
输出：[["X","X","X","X"],["X","X","X","X"],["X","X","X","X"],["X","O","X","X"]]
思路：从边界 'O' DFS 标记为 '#'，然后遍历矩阵，'O'→'X'，'#'→'O'。
时间复杂度：O(m*n)
空间复杂度：O(m*n)（递归栈最坏情况）
"""


def solve(board: list[list[str]]) -> None:
    m: int = len(board)
    n: int = len(board[0])

    def dfs(i: int, j: int) -> None:
        """将与边界连通的 'O' 标记为 '#'（临时标记）"""
        # 越界或当前不是 'O' 则返回
        if i < 0 or i >= m or j < 0 or j >= n or board[i][j] != 'O':
            return
        board[i][j] = '#'  # 临时标记，表示该 'O' 与边界连通，不应被填充

        # 四个方向 DFS 扩散
        dfs(i + 1, j)
        dfs(i - 1, j)
        dfs(i, j + 1)
        dfs(i, j - 1)

    # 第一遍扫描：从四个边界出发，标记所有与边界相连的 'O'
    for i in range(m):
        if board[i][0] == 'O':
            dfs(i, 0)           # 左边界
        if board[i][n - 1] == 'O':
            dfs(i, n - 1)       # 右边界
    for j in range(n):
        if board[0][j] == 'O':
            dfs(0, j)           # 上边界
        if board[m - 1][j] == 'O':
            dfs(m - 1, j)       # 下边界

    # 第二遍扫描：'O' 变成 'X'（被围绕），'#' 恢复为 'O'（边界连通）
    for i in range(m):
        for j in range(n):
            match board[i][j]:  # Python 3.10+ match-case 模式匹配
                case 'O':
                    board[i][j] = 'X'
                case '#':
                    board[i][j] = 'O'


if __name__ == "__main__":
    board = [
        ["X", "X", "X", "X"],
        ["X", "O", "O", "X"],
        ["X", "X", "O", "X"],
        ["X", "O", "X", "X"],
    ]
    solve(board)
    expected = [
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "O", "X", "X"],
    ]
    assert board == expected
    # 单个元素
    board2 = [["X"]]
    solve(board2)
    assert board2 == [["X"]]
