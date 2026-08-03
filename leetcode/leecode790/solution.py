"""
考点：动态规划
题目：Domino and Tromino Tiling（多米诺和托米诺平铺）
题目描述：用 2x1 多米诺和 L 形托米诺平铺 2xn 面板，求方案数 mod 10^9+7。
思路：DP。递推公式：dp[i] = 2 * dp[i-1] + dp[i-3]（i>=3）。dp[0]=1, dp[1]=1, dp[2]=2。用滚动变量优化。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def numTilings(n: int) -> int:
    MOD = 10**9 + 7

    if n == 1:
        return 1
    if n == 2:
        return 2

    # 用三个变量滚动记录 dp[i-3], dp[i-2], dp[i-1]
    dp0 = 1  # dp[0] = 1
    dp1 = 1  # dp[1] = 1
    dp2 = 2  # dp[2] = 2

    # 从 n=3 开始递推
    for _ in range(3, n + 1):
        # dp[i] = 2 * dp[i-1] + dp[i-3]
        dp3 = (2 * dp2 + dp0) % MOD
        # 滚动更新：dp0 → dp1, dp1 → dp2, dp2 → dp3
        dp0, dp1, dp2 = dp1, dp2, dp3

    return dp2


if __name__ == "__main__":
    # 示例：n=3 → 输出: 5
    assert numTilings(3) == 5
    # 示例：n=1 → 输出: 1
    assert numTilings(1) == 1
    # 示例：n=2 → 输出: 2
    assert numTilings(2) == 2
