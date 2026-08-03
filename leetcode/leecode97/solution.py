"""
考点: String, Dynamic Programming
题目: Interleaving String（交错字符串）
题目描述: 验证 s3 是否由 s1 和 s2 交错组成（保持各自字符顺序）。
示例: s1="aabcc", s2="dbbca", s3="aadbbcbcac" -> true
示例: s1="aabcc", s2="dbbca", s3="aadbbbaccc" -> false
思路: 动态规划。dp[i][j] 表示 s1[0..i) 和 s2[0..j) 能否交错组成 s3[0..i+j)。
      dp[i][j] = (s1[i-1]==s3[i+j-1] && dp[i-1][j]) || (s2[j-1]==s3[i+j-1] && dp[i][j-1])。
      空间优化为一维数组。
时间复杂度: O(m * n)
空间复杂度: O(n)
"""


def isInterleave(s1: str, s2: str, s3: str) -> bool:
    m = len(s1)
    n = len(s2)

    # 长度必须匹配
    if m + n != len(s3):
        return False

    # dp[j] 表示 s1[0..i) 和 s2[0..j) 能否交错组成 s3[0..i+j)
    dp = [False] * (n + 1)
    dp[0] = True  # 两个空字符串可以交错组成空字符串

    # 初始化第一行: s1 为空时，只有 s2 与 s3 逐字符匹配才行
    for j in range(1, n + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]

    # 逐行计算
    for i in range(1, m + 1):
        # 每行第一列: s2 为空时，只有 s1 与 s3 逐字符匹配才行
        # 注意: dp[0] 此时代表上一行的 dp[0]（即 s1[0..i-1) 与空 s2 的结果）
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]

        for j in range(1, n + 1):
            # dp[j] 有两种可能:
            # 1. s3 当前字符来自 s1: 需要 s1[i-1]==s3[i+j-1] 且上一行的 dp[j] 为 True
            # 2. s3 当前字符来自 s2: 需要 s2[j-1]==s3[i+j-1] 且左边的 dp[j-1] 为 True
            # 注意: 此时 dp[j] 还是上一行的值（代表 i-1 行），dp[j-1] 已经是当前行的值
            dp[j] = (s1[i - 1] == s3[i + j - 1] and dp[j]) or \
                    (s2[j - 1] == s3[i + j - 1] and dp[j - 1])

    return dp[n]


if __name__ == "__main__":
    assert isInterleave("aabcc", "dbbca", "aadbbcbcac") is True
    assert isInterleave("aabcc", "dbbca", "aadbbbaccc") is False
    assert isInterleave("", "", "") is True
    assert isInterleave("a", "", "a") is True
    assert isInterleave("", "b", "a") is False
