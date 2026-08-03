"""
考点：数组、动态规划、矩阵
题目：Maximal Square（最大正方形）
题目描述：在由 '0' 和 '1' 组成的二维矩阵中，找出只包含 '1' 的最大正方形面积。
  示例：matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]] → 4
思路：动态规划。dp[i][j] 表示以 (i,j) 为右下角的最大正方形边长。
  若 matrix[i][j] == '1'：
    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
  空间优化：只需 O(n) 一行 dp 数组 + 左上角变量。
时间复杂度：O(m*n)
空间复杂度：O(n)
"""


def maximalSquare(matrix: list[list[str]]) -> int:
    m = len(matrix)
    n = len(matrix[0])

    # dp[j]：当前行以 (i, j) 为右下角的最大正方形边长
    dp = [0] * (n + 1)  # 多一列方便处理边界
    max_side = 0  # 记录最大边长
    prev = 0  # 等价于 dp[i-1][j-1]，即左上角的值

    for i in range(m):
        for j in range(n):
            temp = dp[j + 1]  # 暂存当前 dp[j+1]（上一行的值），作为下一轮的左上角
            if matrix[i][j] == "1":
                # 状态转移：取左、上、左上三者的最小值 + 1
                # dp[j] 是左邻居（当前轮已更新），dp[j+1] 是上邻居（上一轮），prev 是左上角
                dp[j + 1] = min(dp[j], dp[j + 1], prev) + 1
                max_side = max(max_side, dp[j + 1])
            else:
                dp[j + 1] = 0  # 当前格子为 '0'，无法构成正方形
            prev = temp  # 更新左上角为下一列使用
        prev = 0  # 每行开头，左上角为 0

    return max_side * max_side  # 面积 = 边长²


if __name__ == "__main__":
    matrix1 = [
        ["1", "0", "1", "0", "0"],
        ["1", "0", "1", "1", "1"],
        ["1", "1", "1", "1", "1"],
        ["1", "0", "0", "1", "0"],
    ]
    assert maximalSquare(matrix1) == 4

    matrix2 = [["0", "1"], ["1", "0"]]
    assert maximalSquare(matrix2) == 1

    matrix3 = [["0"]]
    assert maximalSquare(matrix3) == 0
