"""
考点：字符串, 动态规划
题目：Longest Common Subsequence（最长公共子序列）
题目描述：给定两个字符串 text1 和 text2，返回它们的最长公共子序列的长度。子序列可以不连续但保持顺序。
思路：经典 LCS DP。dp[i][j] 表示 text1[0..i-1] 和 text2[0..j-1] 的 LCS 长度。相等则 dp[i][j]=dp[i-1][j-1]+1；否则 dp[i][j]=max(dp[i-1][j], dp[i][j-1])。
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""


def longestCommonSubsequence(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    # dp[i][j] 表示 text1 前 i 个字符与 text2 前 j 个字符的 LCS 长度
    # 多一行一列初始化为 0，简化边界处理
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                # 字符相等：两个字符都加入 LCS，长度 = 前一对字符的 LCS 长度 + 1
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 字符不等：去掉 text1 的最后一个字符 或 去掉 text2 的最后一个字符，取较大值
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


if __name__ == "__main__":
    # 示例：text1="abcde", text2="ace" → 输出: 3（"ace"）
    assert longestCommonSubsequence("abcde", "ace") == 3
    # 示例：text1="abc", text2="def" → 输出: 0
    assert longestCommonSubsequence("abc", "def") == 0
    # 示例：text1="abc", text2="abc" → 输出: 3
    assert longestCommonSubsequence("abc", "abc") == 3
