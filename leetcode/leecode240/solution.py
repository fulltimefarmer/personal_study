"""
考点：数组、二分查找、分治、矩阵
题目：Search a 2D Matrix II（搜索二维矩阵 II）
思路：从右上角开始，matrix[row][col]>target 左移，<target 下移，每次排除一行或一列。
时间复杂度：O(m + n)
空间复杂度：O(1)
"""


def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    m = len(matrix)
    n = len(matrix[0])
    row = 0
    col = n - 1  # 从右上角开始搜索

    while row < m and col >= 0:
        if matrix[row][col] == target:
            return True
        elif matrix[row][col] > target:
            # 当前值大于 target，由于每列递增，整列右侧都大于 target
            col -= 1  # 左移排除当前列
        else:
            # 当前值小于 target，由于每行递增，整行左侧都小于 target
            row += 1  # 下移排除当前行

    return False


if __name__ == "__main__":
    # 示例 1: 在矩阵中找到 5
    matrix = [[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22],
              [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]]
    assert searchMatrix(matrix, 5) is True
    # 示例 2: 在矩阵中找不到 20
    assert searchMatrix(matrix, 20) is False
    print("全部测试通过")
