"""
考点：字符串、动态规划、递归
题目：Regular Expression Matching（正则表达式匹配）
思路：动态规划，dp[i][j] 表示 s 的前 i 个字符与 p 的前 j 个字符是否匹配，根据当前模式字符分情况转移
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""

def isMatch(s: str, p: str) -> bool:
    m, n = len(s), len(p)

    # dp[i][j] 表示 s 的前 i 个字符（s[0..i-1]）与 p 的前 j 个字符（p[0..j-1]）是否匹配
    # 列表推导式嵌套：外层循环 m+1 次，每次生成 n+1 个 False 的列表
    dp: list[list[bool]] = [[False] * (n + 1) for _ in range(m + 1)]

    # 空字符串和空模式匹配
    dp[0][0] = True

    # 初始化：处理 s 为空、p 非空的情况
    # 例如 s="" 可以匹配 p="a*" 因为 * 可以消去前面的 a
    for j in range(2, n + 1):
        if p[j - 1] == "*":
            # 当 p[j-1] 是 * 时，dp[0][j] 取决于去掉 "x*" 两个字符后的匹配结果
            # 即 * 让前面的字符出现 0 次
            dp[0][j] = dp[0][j - 2]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # 情况 1：当前字符匹配（相同 或 模式是 .）
            if p[j - 1] == s[i - 1] or p[j - 1] == ".":
                dp[i][j] = dp[i - 1][j - 1]
            elif p[j - 1] == "*":
                # 情况 2：* 让前面的字符出现 0 次，跳过 "x*"
                dp[i][j] = dp[i][j - 2]
                # 情况 3：* 让前面的字符出现 1 次或多次
                # 条件：* 前面的字符（p[j-2]）与 s 当前字符匹配
                if p[j - 2] == s[i - 1] or p[j - 2] == ".":
                    # dp[i-1][j] 表示 s 去掉当前字符后，"x*" 仍然能匹配（即 * 匹配多次）
                    dp[i][j] = dp[i][j] or dp[i - 1][j]

    return dp[m][n]

if __name__ == "__main__":
    assert isMatch("aa", "a") == False
    assert isMatch("aa", "a*") == True
    assert isMatch("ab", ".*") == True
    assert isMatch("aab", "c*a*b") == True
    assert isMatch("mississippi", "mis*is*p*.") == False
    print("全部通过 ✓")
