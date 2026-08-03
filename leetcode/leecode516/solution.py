"""
考点：字符串, 动态规划
题目：Longest Palindromic Subsequence（最长回文子序列）
题目描述：给定字符串 s，求最长回文子序列的长度。子序列可以不连续。
思路：区间 DP。dp[i][j] 表示 s[i..j] 的最长回文子序列长度。若 s[i]==s[j]，dp[i][j]=dp[i+1][j-1]+2；否则 dp[i][j]=max(dp[i+1][j], dp[i][j-1])。
时间复杂度：O(n²)
空间复杂度：O(n²)
"""


def longestPalindromeSubseq(s: str) -> int:
    n = len(s)
    # dp[i][j] 表示子串 s[i..j] 中最长回文子序列的长度
    dp = [[0] * n for _ in range(n)]

    # 从右向左遍历 i，因为 dp[i+1][j-1] 依赖于 i+1，需要先计算较大的 i
    for i in range(n - 1, -1, -1):
        dp[i][i] = 1  # 单个字符自身就是长度为 1 的回文
        # j 从 i+1 到 n-1，从小到大扩展
        for j in range(i + 1, n):
            if s[i] == s[j]:
                # 首尾相同，回文长度 = 去掉首尾的子串的回文长度 + 2
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                # 首尾不同，取删掉左边或删掉右边后的最大值
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return dp[0][n - 1]


if __name__ == "__main__":
    # 示例："bbbab" → 输出: 4（"bbbb"）
    assert longestPalindromeSubseq("bbbab") == 4
    # 示例："cbbd" → 输出: 2（"bb"）
    assert longestPalindromeSubseq("cbbd") == 2
