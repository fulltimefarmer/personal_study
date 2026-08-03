"""
考点: Array, Math, Matrix
题目: Rotate Image（旋转图像）
题目描述: n×n矩阵原地顺时针旋转90°。如 [[1,2,3],[4,5,6],[7,8,9]] -> [[7,4,1],[8,5,2],[9,6,3]]
思路: 先转置（对角线交换），再水平翻转（每行反转）。两步都是原地操作。
时间复杂度: O(n^2)
空间复杂度: O(1)
"""

from typing import List


def rotate(matrix: List[List[int]]) -> None:
    """
    Do not return anything, modify matrix in-place instead.
    """
    n = len(matrix)

    # 步骤一: 沿主对角线转置，只遍历上三角避免重复交换
    for i in range(n):
        # j 从 i+1 开始，确保只交换对角线右上方的元素
        for j in range(i + 1, n):
            # Python 的元组打包/解包交换变量，无需临时变量
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # 步骤二: 水平翻转，即反转每行
    for i in range(n):
        # 只遍历行左半部分，与右半部分对称交换
        for j in range(n // 2):  # n // 2 表示整数除法，等价于 Math.floor(n / 2)
            # n - 1 - j 是对称位置: 第 j 列 -> 倒数第 j 列的索引
            matrix[i][j], matrix[i][n - 1 - j] = matrix[i][n - 1 - j], matrix[i][j]


if __name__ == "__main__":
    m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    rotate(m1)
    assert m1 == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]

    m2 = [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]
    rotate(m2)
    assert m2 == [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]
