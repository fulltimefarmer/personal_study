"""
考点: Array, String, Backtracking, Matrix, DFS
题目: Word Search（单词搜索）
题目描述: 给定 m*n 字符网格 board 和单词 word，判断单词是否存在于网格中。
      字母需按相邻单元格顺序连接，同一单元格不可重复使用。
示例: board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED" -> true
思路: DFS 回溯。从每个格子出发搜索，标记已访问（原地字符替换），四个方向递归，回溯恢复。
时间复杂度: O(m * n * 4^L)
空间复杂度: O(L)  L 为单词长度（递归深度）
"""


def exist(board: list[list[str]], word: str) -> bool:
    m = len(board)
    n = len(board[0])

    def dfs(i: int, j: int, index: int) -> bool:
        # 所有字符都已匹配成功
        if index == len(word):
            return True
        # 边界检查 + 字符不匹配 + 已访问检查
        if i < 0 or i >= m or j < 0 or j >= n or board[i][j] != word[index]:
            return False

        # 原地标记访问: 暂存原字符并替换为特殊标记
        # 这避免了额外 visited 数组，节省空间
        temp = board[i][j]
        board[i][j] = '#'  # 用 '#' 标记已访问（题目只含大小写字母）

        # 四个方向 DFS 搜索，用 or 短路: 任一路径找到即可
        # Python 的逻辑或 or 具有短路特性，找到后不再尝试后续方向
        found = (
            dfs(i + 1, j, index + 1) or  # 下
            dfs(i - 1, j, index + 1) or  # 上
            dfs(i, j + 1, index + 1) or  # 右
            dfs(i, j - 1, index + 1)     # 左
        )

        # 回溯: 恢复原字符
        board[i][j] = temp
        return found

    # 从每个格子作为起点尝试
    for i in range(m):
        for j in range(n):
            if dfs(i, j, 0):
                return True

    return False


if __name__ == "__main__":
    board1 = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    assert exist(board1, "ABCCED") is True
    assert exist(board1, "SEE") is True
    assert exist(board1, "ABCB") is False

    assert exist([["a"]], "a") is True
    assert exist([["a"]], "b") is False
