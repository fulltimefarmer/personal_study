"""
考点: Array, Matrix, Simulation
题目: Spiral Matrix（螺旋矩阵）
题目描述: 给定 m*n 矩阵，按顺时针螺旋顺序返回所有元素。
示例: matrix = [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5]
思路: 定义 top/bottom/left/right 四个边界，按 右->下->左->上 顺序遍历，每走完一条边收缩边界。
      注意在反向遍历前需检查边界条件，防止重复。
时间复杂度: O(m * n)
空间复杂度: O(1)
"""


def spiralOrder(matrix: list[list[int]]) -> list[int]:
    if not matrix:
        return []

    result: list[int] = []
    # 定义四个边界: top/left 初始为 0, bottom/right 初始为最后一行/列
    top = 0
    bottom = len(matrix) - 1
    left = 0
    right = len(matrix[0]) - 1

    # 当上下或左右边界未交错时继续遍历
    while top <= bottom and left <= right:
        # 向右遍历: 从 (top, left) 到 (top, right)
        # range(left, right + 1) 生成 [left, right] 范围的整数
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1  # 最上面一行已访问，上边界下移

        # 向下遍历: 从 (top, right) 到 (bottom, right)
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1  # 最右边一列已访问，右边界左移

        # 向左遍历前检查: 避免上下边界交错时重复遍历
        if top <= bottom:
            # range(right, left - 1, -1): 从 right 递减到 left
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1

        # 向上遍历前检查: 避免左右边界交错时重复遍历
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1

    return result


if __name__ == "__main__":
    assert spiralOrder([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert spiralOrder([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    assert spiralOrder([[3], [2]]) == [3, 2]
