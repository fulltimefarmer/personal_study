"""
考点：贪心、递归、字符串、动态规划
题目：Wildcard Matching（通配符匹配）
思路：动态规划，dp[i][j] 表示 s 的前 i 个字符与 p 的前 j 个字符是否匹配，分 '*' / '?' / 普通字符三种情况转移
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""

def isMatch(s: str, p: str) -> bool:
    m, n = len(s), len(p)

    # dp[i][j] 表示 s[0..i-1] 与 p[0..j-1] 是否匹配
    # 列表推导式：m+1 行 n+1 列，全部初始化为 False
    dp: list[list[bool]] = [[False] * (n + 1) for _ in range(m + 1)]

    # 空字符串匹配空模式
    dp[0][0] = True

    # 初始化第一行：s 为空，p 非空的情况
    # 只有当 p 的前 j 个字符全为 '*' 时才能匹配空字符串
    for j in range(1, n + 1):
        if p[j - 1] == "*":
            # dp[0][j] 继承 dp[0][j-1] 的结果
            # 即 '*' 可以匹配空字符串（忽略 '*' 本身）
            dp[0][j] = dp[0][j - 1]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j - 1] == "*":
                # '*' 有两种选择：
                # 1. '*' 匹配空字符串：dp[i][j - 1]（忽略 '*'）
                # 2. '*' 匹配一个或多个字符：dp[i - 1][j]（用 '*' 消耗 s 的一个字符）
                dp[i][j] = dp[i - 1][j] or dp[i][j - 1]
            elif p[j - 1] == "?" or p[j - 1] == s[i - 1]:
                # '?' 匹配任意单字符，或普通字符精确匹配
                # 取决于前一个位置 dp[i-1][j-1]
                dp[i][j] = dp[i - 1][j - 1]
            # 否则 p[j-1] 是普通字符且与 s[i-1] 不匹配，dp[i][j] 保持 False

    return dp[m][n]

if __name__ == "__main__":
    assert isMatch("aa", "a") == False
    assert isMatch("aa", "*") == True
    assert isMatch("cb", "?a") == False
    assert isMatch("adceb", "*a*b") == True
    assert isMatch("acdcb", "a*c?b") == False
    assert isMatch("", "****") == True
    print("全部通过 ✓")
