"""
考点: Array, Hash Table, Matrix
题目: Set Matrix Zeroes（矩阵置零）
题目描述: 给定 m*n 矩阵，若元素为 0，将其所在行和列全部置零。要求原地算法，O(1) 额外空间。
示例: matrix = [[1,1,1],[1,0,1],[1,1,1]] -> [[1,0,1],[0,0,0],[1,0,1]]
思路: 利用第一行和第一列作为标记。先记录第一行/第一列是否需要置零，
      再用它们标记需要置零的行列，最后根据标记置零。
时间复杂度: O(m * n)
空间复杂度: O(1)
"""


def setZeroes(matrix: list[list[int]]) -> None:
    """
    Do not return anything, modify matrix in-place instead.
    """
    if not matrix:
        return

    m = len(matrix)
    n = len(matrix[0])

    # 步骤一: 用两个布尔变量记录第一行和第一列自身是否需要置零
    # 使用 Python 3.12 的 | 类型联合语法（等价于 typing.Union[bool, None]）
    first_row_zero = False
    first_col_zero = False

    # 检查第一行是否有 0
    for j in range(n):
        if matrix[0][j] == 0:
            first_row_zero = True
            break

    # 检查第一列是否有 0
    for i in range(m):
        if matrix[i][0] == 0:
            first_col_zero = True
            break

    # 步骤二: 用第一行和第一列作为标记数组
    # 遍历剩余矩阵(i>=1, j>=1)，发现 0 就在对应的第一行第一列做标记
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][j] == 0:
                matrix[i][0] = 0  # 标记该行需要置零
                matrix[0][j] = 0  # 标记该列需要置零

    # 步骤三: 根据标记置零内部矩阵（第一行第一列留到最后处理）
    for i in range(1, m):
        for j in range(1, n):
            # 如果该行或该列被标记了，则当前位置置零
            if matrix[i][0] == 0 or matrix[0][j] == 0:
                matrix[i][j] = 0

    # 步骤四: 最后处理第一行和第一列
    if first_row_zero:
        for j in range(n):
            matrix[0][j] = 0

    if first_col_zero:
        for i in range(m):
            matrix[i][0] = 0


if __name__ == "__main__":
    m1 = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    setZeroes(m1)
    assert m1 == [[1, 0, 1], [0, 0, 0], [1, 0, 1]]

    m2 = [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]]
    setZeroes(m2)
    assert m2 == [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]]

    m3 = [[1, 2, 3, 4], [5, 0, 7, 8], [9, 10, 11, 12]]
    setZeroes(m3)
    assert m3 == [[1, 0, 3, 4], [0, 0, 0, 0], [9, 0, 11, 12]]
