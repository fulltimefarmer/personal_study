"""
考点: String, Dynamic Programming
题目: Edit Distance（编辑距离）
题目描述: 给定两个单词 word1 和 word2，返回将 word1 转换为 word2 的最少操作数（插入、删除、替换）。
示例: word1 = "horse", word2 = "ros" -> 3
示例: word1 = "intention", word2 = "execution" -> 5
思路: 动态规划（Levenshtein 距离）。
      dp[i][j]: word1[0..i) 转 word2[0..j) 的最少操作数。
      若 word1[i-1]==word2[j-1]，dp[i][j]=dp[i-1][j-1]；
      否则 dp[i][j]=1+min(dp[i-1][j](删), dp[i][j-1](插), dp[i-1][j-1](换))。
时间复杂度: O(m * n)
空间复杂度: O(n)
"""


def minDistance(word1: str, word2: str) -> int:
    m = len(word1)
    n = len(word2)

    # 初始化一维 dp 数组: dp[j] 表示 word2 前 j 个字符需要 j 次插入
    # 即 word1 为空时的编辑距离
    dp = [j for j in range(n + 1)]  # [0, 1, 2, ..., n] 的列表推导式写法

    # 逐行计算
    for i in range(1, m + 1):
        # prev 保存左上角的值 dp[i-1][j-1]
        prev = dp[0]
        # dp[0] 表示 word1 前 i 个字符删除为空需要的次数
        dp[0] = i

        for j in range(1, n + 1):
            # temp 暂存旧的 dp[j]（即 dp[i-1][j]），备用作为下一个 prev
            temp = dp[j]

            if word1[i - 1] == word2[j - 1]:
                # 当前字符相同，无需操作，编辑距离 = 左上角的值
                dp[j] = prev
            else:
                # 取三种操作的最小值:
                # prev = dp[i-1][j-1] 替换
                # dp[j] = dp[i-1][j]   删除
                # dp[j-1] = dp[i][j-1] 插入
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])

            prev = temp  # 更新左上角为下一轮准备

    return dp[n]


if __name__ == "__main__":
    assert minDistance("horse", "ros") == 3
    assert minDistance("intention", "execution") == 5
    assert minDistance("", "a") == 1
    assert minDistance("abc", "abc") == 0
