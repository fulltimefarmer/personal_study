"""
考点: Math, Dynamic Programming, Combinatorics
题目: Unique Paths（不同路径）
题目描述: 机器人位于 m*n 网格左上角，每次只能向下或向右移动，求到达右下角的不同路径数。
示例: m = 3, n = 7 -> 28
示例: m = 3, n = 2 -> 3
思路: 动态规划。dp[i][j] = dp[i-1][j] + dp[i][j-1]，空间优化为一维数组。
      也可用组合数学: C(m+n-2, m-1)。
时间复杂度: O(m * n)
空间复杂度: O(n)
"""


def uniquePaths(m: int, n: int) -> int:
    # 初始化一维 dp 数组，全部为 1
    # 第一行所有格子都只有一种走法（一直向右）
    dp = [1] * n  # [1] * n 创建长度为 n 且元素全为 1 的列表

    # 从第二行开始计算
    for i in range(1, m):
        # 从第二列开始，dp[j] = 上方的值(即旧的dp[j]) + 左侧的值(dp[j-1])
        # dp[j] 在被覆盖前代表上一行的 dp[j]，加上 dp[j-1]（当前行左边的值）
        for j in range(1, n):
            # dp[j] 原地累加: 当前的 dp[j] 是上一行的值(上方)，dp[j-1] 是本行刚算好的值(左方)
            dp[j] += dp[j - 1]

    # 最终答案在 dp 数组最后一个元素
    return dp[n - 1]


if __name__ == "__main__":
    assert uniquePaths(3, 7) == 28
    assert uniquePaths(3, 2) == 3
    assert uniquePaths(1, 1) == 1
