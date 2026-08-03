"""
考点：二分查找、分治、矩阵
题目：Search a 2D Matrix II（搜索二维矩阵 II）
题目描述：在每行递增、每列也递增的 m×n 矩阵中查找目标值 target。
  示例：matrix = [[1,4,7,11,15],[2,5,8,12,19],[3,6,9,16,22],[10,13,14,17,24],[18,21,23,26,30]], target = 5 → true
思路：Z 字形搜索。从右上角出发：
  如果当前值 > target，则向左移动（列-1，因为当前列下面的值更大）
  如果当前值 < target，则向下移动（行+1，因为当前行左边的值更小）
  如果相等则找到。
时间复杂度：O(m + n)
空间复杂度：O(1)
"""


def searchMatrix(matrix: list[list[int]], target: int) -> bool:
    m = len(matrix)
    n = len(matrix[0])

    # 从右上角开始搜索（利用行列有序的特性，像走阶梯一样排除）
    row = 0
    col = n - 1

    while row < m and col >= 0:
        current = matrix[row][col]
        if current == target:
            return True
        elif current > target:
            # 当前值大于 target，目标不可能在当前列（当前列下面元素更大）
            col -= 1
        else:
            # 当前值小于 target，目标不可能在当前行（当前行左边元素更小）
            row += 1

    return False


if __name__ == "__main__":
    matrix = [
        [1, 4, 7, 11, 15],
        [2, 5, 8, 12, 19],
        [3, 6, 9, 16, 22],
        [10, 13, 14, 17, 24],
        [18, 21, 23, 26, 30],
    ]
    assert searchMatrix(matrix, 5) is True
    assert searchMatrix(matrix, 20) is False
    assert searchMatrix(matrix, 1) is True
    assert searchMatrix(matrix, 30) is True
