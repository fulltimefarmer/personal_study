"""
考点：数组、矩阵、模拟
题目：Game of Life（生命游戏）—— LeetCode 289
题目描述：根据 Conway 生命游戏规则同时更新每个细胞，要求原地操作
思路：用复合状态编码避免覆盖原始信息。
      -1: 活→死, 2: 死→活。遍历时判断原始状态（1 或 -1 都是原来活）。
      最后将所有 -1 变 0，2 变 1。
时间复杂度：O(m × n)
空间复杂度：O(1)
"""

def gameOfLife(board: list[list[int]]) -> None:
    m: int = len(board)
    n: int = len(board[0])

    # 8 个方向的偏移量：分别对应左上、上、右上、左、右、左下、下、右下
    directions: list[tuple[int, int]] = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ]

    # 第一遍遍历：用复合状态标记变化
    for i in range(m):
        for j in range(n):
            live_neighbors = 0
            for dx, dy in directions:
                ni, nj = i + dx, j + dy
                if 0 <= ni < m and 0 <= nj < n:
                    # abs(board[ni][nj]) == 1 判断原始是否为活细胞
                    # 1 (原本活) 和 -1 (活→死) 的绝对值都是 1
                    if abs(board[ni][nj]) == 1:
                        live_neighbors += 1

            # 规则应用（用 match-case 匹配 Python 3.10+ 语法）
            match board[i][j]:
                case 1 if live_neighbors < 2 or live_neighbors > 3:
                    board[i][j] = -1  # 活细胞死亡
                case 0 if live_neighbors == 3:
                    board[i][j] = 2   # 死细胞复活
                case _:
                    pass  # 其他情况保持不变

    # 第二遍遍历：将复合状态还原为 0/1
    for i in range(m):
        for j in range(n):
            if board[i][j] == -1:
                board[i][j] = 0  # 活→死，最终为死
            elif board[i][j] == 2:
                board[i][j] = 1  # 死→活，最终为活


if __name__ == "__main__":
    board1 = [[0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 0, 0]]
    gameOfLife(board1)
    assert board1 == [[0, 0, 0], [1, 0, 1], [0, 1, 1], [0, 1, 0]]

    board2 = [[1, 1], [1, 0]]
    gameOfLife(board2)
    assert board2 == [[1, 1], [1, 1]]

    print("所有断言通过！")
