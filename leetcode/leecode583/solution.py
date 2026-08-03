"""
考点：字符串, 动态规划
题目：Delete Operation for Two Strings（两个字符串的删除操作）
题目描述：给定 word1 和 word2，每步可删除任意一个字符串的一个字符。求使两个字符串相同的最少步数。
思路：最小删除步数 = len1 + len2 - 2 * LCS。先求最长公共子序列长度，再用总长度减去两倍 LCS 得到最少删除步数。
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""


def minDistance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    # dp[i][j] 表示 word1 前 i 个字符与 word2 前 j 个字符的最长公共子序列长度
    # dp 大小为 (m+1) x (n+1)，第 0 行/列为空串，初始为 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                # 字符相等：从前一对字符的 LCS 长度 + 1
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 字符不等：取去掉 word1 最后一个字符 或 去掉 word2 最后一个字符 的较大值
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs = dp[m][n]
    # 最少删除步数 = 两字符串总长度 - 两倍的最长公共子序列长度
    return m + n - 2 * lcs


if __name__ == "__main__":
    # 示例："sea", "eat" → 输出: 2（删 s 和 t，保留 "ea"）
    assert minDistance("sea", "eat") == 2
    # 示例："leetcode", "etco" → 输出: 4
    assert minDistance("leetcode", "etco") == 4
