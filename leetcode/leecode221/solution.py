"""
考点：数组、动态规划、矩阵
题目：Maximal Square（最大正方形）
思路：DP，dp[i][j]=min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])+1（当 matrix[i][j]=='1'）。
      一维 DP 优化空间。
时间复杂度：O(m × n)
空间复杂度：O(n)
"""


def maximalSquare(matrix: list[list[str]]) -> int:
    m = len(matrix)
    n = len(matrix[0])
    # dp[j+1] 表示以当前行第 j 列为右下角的最大正方形边长
    dp = [0] * (n + 1)
    max_side = 0

    for i in range(m):
        prev = 0  # 保存 dp[i-1][j-1]（即上一行前一列的值）
        for j in range(n):
            temp = dp[j + 1]  # 暂存 dp[i-1][j+1] 即上一行当前列的值
            if matrix[i][j] == "1":
                # 关键 DP 转移：取左、上、左上三个方向的最小值+1
                # dp[j]       → 左边 (dp[i][j-1])
                # dp[j+1]     → 上边 (dp[i-1][j])
                # prev        → 左上 (dp[i-1][j-1])
                dp[j + 1] = min(dp[j], dp[j + 1], prev) + 1
                max_side = max(max_side, dp[j + 1])
            else:
                dp[j + 1] = 0  # 当前位置为 '0'，无法构成正方形
            prev = temp  # 更新 prev 为下一列做准备

    return max_side * max_side  # 面积 = 边长²


if __name__ == "__main__":
    # 示例: 最大正方形面积为 4
    matrix = [
        ["1", "0", "1", "0", "0"],
        ["1", "0", "1", "1", "1"],
        ["1", "1", "1", "1", "1"],
        ["1", "0", "0", "1", "0"],
    ]
    assert maximalSquare(matrix) == 4
    print("全部测试通过")
