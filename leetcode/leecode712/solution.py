"""
考点：字符串, 动态规划
题目：Minimum ASCII Delete Sum for Two Strings（两个字符串的最小ASCII删除和）
题目描述：给定 s1 和 s2，求使两字符串相等所需删除字符的 ASCII 值的最小和。
思路：DP。dp[i][j] 使 s1[0..i] 和 s2[0..j] 相等的最小删除和。相等时 dp[i][j]=dp[i-1][j-1]；否则 min(删s1[i], 删s2[j])。
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""


def minimumDeleteSum(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    # dp[i][j] 表示使 s1 前 i 个字符和 s2 前 j 个字符相等的最小 ASCII 删除和
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 初始化第一列：s2 为空串时，需要删除 s1 的所有字符
    for i in range(1, m + 1):
        # ord(ch) 获取字符的 ASCII 码值
        dp[i][0] = dp[i - 1][0] + ord(s1[i - 1])

    # 初始化第一行：s1 为空串时，需要删除 s2 的所有字符
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] + ord(s2[j - 1])

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                # 字符相等，不需要删除，和前一状态相同
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # 字符不等，选择删除 s1 的当前字符 或 s2 的当前字符，取较小值
                dp[i][j] = min(dp[i - 1][j] + ord(s1[i - 1]), dp[i][j - 1] + ord(s2[j - 1]))

    return dp[m][n]


if __name__ == "__main__":
    # 示例："sea", "eat" → 输出: 231（s1 删 's'(115) + s2 删 't'(116) = 231，保留 "ea"）
    assert minimumDeleteSum("sea", "eat") == 231
    # 示例："delete", "leet" → 输出: 403
    assert minimumDeleteSum("delete", "leet") == 403
