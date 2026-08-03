"""
考点：String, Dynamic Programming
题目：Distinct Subsequences（不同的子序列）
题目描述：给定字符串 s 和 t，计算 s 的子序列中 t 出现的个数，对 10^9+7 取模。
示例 1：s = "rabbbit", t = "rabbit"，输出 3
示例 2：s = "babgbag", t = "bag"，输出 5
思路：DP，dp[j] 表示 s[0..i-1] 的子序列中 t[0..j-1] 出现的次数（滚动数组）。
若 s[i-1]==t[j-1]，dp[j]=dp[j-1]+dp[j]；否则 dp[j]=dp[j]。
初始化 dp[0]=1（空串是任何串的子序列）。
时间复杂度：O(m*n)
空间复杂度：O(n)（滚动数组优化）
"""
MOD: int = 10**9 + 7


def numDistinct(s: str, t: str) -> int:
    m, n = len(s), len(t)
    # dp[j] 表示 s 的前缀中 t[0..j-1] 出现的次数
    # 使用滚动数组，一维即可，但需要从右往左更新
    dp: list[int] = [0] * (n + 1)
    dp[0] = 1  # 空串匹配任何 s 前缀一次（不选任何字符）

    for i in range(1, m + 1):
        # 内层循环必须从右向左更新，因为 dp[j] 依赖上一行的 dp[j-1]（左上角值）
        # 如果从左向右，dp[j-1] 已经被当前行更新过，会出错
        for j in range(n, 0, -1):
            if s[i - 1] == t[j - 1]:
                # 两种情况之和：使用 s[i-1] 匹配 t[j-1] + 不使用 s[i-1]
                # dp[j] 是上一行的值（不使用），dp[j-1] 也是上一行的值（使用，因为从右向左）
                dp[j] = (dp[j] + dp[j - 1]) % MOD
            # 不相等时 dp[j] 保持不变（继承上一行的值）

    return dp[n]


if __name__ == "__main__":
    assert numDistinct("rabbbit", "rabbit") == 3
    assert numDistinct("babgbag", "bag") == 5
    assert numDistinct("", "a") == 0
    assert numDistinct("a", "") == 1
