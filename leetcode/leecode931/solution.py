"""
考点：数组, 动态规划, 矩阵
题目：Minimum Falling Path Sum（下降路径最小和）
题目描述：n x n 矩阵，下降路径从第一行任意位置开始，每行可选正下方、左下或右下元素。求下降路径的最小和。
思路：DP。dp[i][j] = matrix[i][j] + min(dp[i-1][j-1], dp[i-1][j], dp[i-1][j+1])。最终 min(dp[n-1])。用滚动数组优化空间到 O(n)。
时间复杂度：O(n²)
空间复杂度：O(n)
"""


def minFallingPathSum(matrix: list[list[int]]) -> int:
    n = len(matrix)
    # prev 表示上一行的 dp 值，初始为第一行
    prev = matrix[0][:]  # [:] 进行浅拷贝，避免修改原矩阵

    for i in range(1, n):
        # curr 存储当前行的 dp 值
        curr = [0] * n
        for j in range(n):
            # 从上一行的正上方、左上方、右上方中取最小值
            min_above = prev[j]
            if j > 0:
                min_above = min(min_above, prev[j - 1])
            if j < n - 1:
                min_above = min(min_above, prev[j + 1])
            # 当前路径和 = 当前格子值 + 上方最小值
            curr[j] = matrix[i][j] + min_above
        prev = curr  # 滚动：当前行成为下一轮的上一行

    return min(prev)


if __name__ == "__main__":
    # 示例：[[2,1,3],[6,5,4],[7,8,9]] → 输出: 13（路径: 1→5→7 或 1→4→8）
    assert minFallingPathSum([[2, 1, 3], [6, 5, 4], [7, 8, 9]]) == 13
    # 示例：[[-19,57],[-40,-5]] → 输出: -59
    assert minFallingPathSum([[-19, 57], [-40, -5]]) == -59
