"""
考点: Math, Dynamic Programming, Memoization
题目: Climbing Stairs（爬楼梯）
题目描述: 爬 n 阶楼梯，每次爬 1 或 2 阶，求不同方法数。
示例: n = 2 -> 2
示例: n = 3 -> 3
思路: 斐波那契数列。dp[n] = dp[n-1] + dp[n-2]，空间优化为 O(1)。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def climbStairs(n: int) -> int:
    if n <= 2:
        return n  # n=1 有 1 种，n=2 有 (1+1, 2) 两种

    # prev2 代表 dp[n-2], prev1 代表 dp[n-1]
    prev2 = 1  # dp[1]
    prev1 = 2  # dp[2]

    # 从第 3 阶开始计算到第 n 阶
    for i in range(3, n + 1):  # range(3, n+1) 生成 3, 4, ..., n
        # 同时赋值: Python 支持一行内多个变量赋值
        # 右边先计算，再同时赋给左边，无需临时变量
        # 新 dp[i] = dp[i-1] + dp[i-2]，然后滚动更新
        prev1, prev2 = prev1 + prev2, prev1

    return prev1


if __name__ == "__main__":
    assert climbStairs(2) == 2
    assert climbStairs(3) == 3
    assert climbStairs(4) == 5
    assert climbStairs(5) == 8
