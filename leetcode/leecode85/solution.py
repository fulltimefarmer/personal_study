"""
考点: Stack, Array, Dynamic Programming, Matrix, Monotonic Stack
题目: Maximal Rectangle（最大矩形）
题目描述: 给定只含 '0' 和 '1' 的二维二进制矩阵，找出只包含 '1' 的最大矩形面积。
示例: matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]] -> 6
思路: 转化为直方图最大矩形问题（LeetCode 84）。逐行构建 heights 数组（连续 1 的高度），
      每行用单调栈计算最大矩形面积，更新全局最大值。
时间复杂度: O(rows * cols)
空间复杂度: O(cols)
"""


def maximalRectangle(matrix: list[list[str]]) -> int:
    if not matrix or not matrix[0]:
        return 0

    cols = len(matrix[0])
    # heights[j] 表示第 j 列中从当前行向上连续的 '1' 的个数
    heights = [0] * cols
    max_area = 0

    for row in matrix:
        # 更新直方图高度
        for j in range(cols):
            if row[j] == '1':
                heights[j] += 1  # 连续 1，高度 +1
            else:
                heights[j] = 0  # 遇到 0，高度归零
        # 对当前行的直方图计算最大矩形面积，更新全局最大
        max_area = max(max_area, _largestRectangleInHistogram(heights))

    return max_area


def _largestRectangleInHistogram(heights: list[int]) -> int:
    """
    辅助函数: 单调递增栈计算直方图最大矩形面积（同 LeetCode 84）
    """
    stack: list[int] = []
    max_area = 0
    # 创建临时副本避免修改原 heights
    h = heights + [0]  # 列表拼接，末尾加哨兵 0

    for i, val in enumerate(h):
        # 当前高度破坏单调递增时，出栈计算面积
        while stack and val < h[stack[-1]]:
            height = h[stack.pop()]
            # 栈为空说明该柱子左侧没有更矮的，当前柱子可延伸到左边界
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)

    return max_area


if __name__ == "__main__":
    matrix1 = [
        ["1", "0", "1", "0", "0"],
        ["1", "0", "1", "1", "1"],
        ["1", "1", "1", "1", "1"],
        ["1", "0", "0", "1", "0"]
    ]
    assert maximalRectangle(matrix1) == 6

    matrix2 = [["0"]]
    assert maximalRectangle(matrix2) == 0

    matrix3 = [["1"]]
    assert maximalRectangle(matrix3) == 1

    matrix4 = [["1", "1"], ["1", "1"]]
    assert maximalRectangle(matrix4) == 4
