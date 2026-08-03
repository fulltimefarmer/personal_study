"""
考点：BFS、数学、动态规划
题目：Perfect Squares（完全平方数）—— LeetCode 279
题目描述：给定整数 n，求最少需要多少个完全平方数相加得到 n
思路：动态规划。dp[i] = min(dp[i - j*j] + 1)，其中 j*j <= i。
时间复杂度：O(n * sqrt(n))
空间复杂度：O(n)
"""

import math


def numSquares(n: int) -> int:
    # dp[i] 表示和为 i 所需的最少完全平方数个数
    # 初始化所有值为正无穷，表示初始状态不可达
    dp = [float("inf")] * (n + 1)
    dp[0] = 0  # 和为 0 需要 0 个完全平方数

    # 预处理所有可能的完全平方数（j*j），避免在内层循环重复计算
    squares = [j * j for j in range(1, int(math.isqrt(n)) + 1)]

    for i in range(1, n + 1):
        for square in squares:
            if square > i:
                break  # 因为 squares 是递增的，后续只会更大
            # 状态转移：使用一个 square 后，剩余部分 i-square 的最优解 + 1
            dp[i] = min(dp[i], dp[i - square] + 1)

    return dp[n]


if __name__ == "__main__":
    assert numSquares(12) == 3  # 4 + 4 + 4
    assert numSquares(13) == 2  # 4 + 9
    assert numSquares(1) == 1
    assert numSquares(2) == 2  # 1 + 1
    assert numSquares(4) == 1  # 4 本身是完全平方数
    print("所有断言通过！")
