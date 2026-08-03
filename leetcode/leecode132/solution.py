"""
考点：String, Dynamic Programming
题目：Palindrome Partitioning II（分割回文串II）
题目描述：将字符串分割成全回文子串，求最少分割次数。
示例 1：s = "aab"，输出 1（["aa","b"]）
示例 2：s = "a"，输出 0
示例 3：s = "ab"，输出 1
思路：DP 预处理回文表，再 DP 求最少分割次数。
is_pal[i][j] 表示 s[i..j] 是否为回文。
dp[i] 表示 s[0..i] 的最少分割次数。
dp[i] = min(dp[i], dp[j-1]+1) 当 s[j..i] 是回文。
时间复杂度：O(n^2)
空间复杂度：O(n^2)
"""


def minCut(s: str) -> int:
    n: int = len(s)

    # 预处理回文表：is_pal[i][j] 表示 s[i..j] 是否为回文
    # 使用列表推导式创建 n×n 的二维布尔列表
    is_pal: list[list[bool]] = [[False] * n for _ in range(n)]

    # 从右往左填表，因为 is_pal[i][j] 依赖 is_pal[i+1][j-1]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            # 回文条件：首尾字符相等，且中间部分是回文（或长度 <= 1）
            if s[i] == s[j] and (j - i <= 1 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True

    # dp[i] 表示 s[0..i] 的最少分割次数
    dp: list[int] = [0] * n

    for i in range(n):
        # 如果整个 s[0..i] 是回文，不需要分割
        if is_pal[0][i]:
            dp[i] = 0
            continue
        # 否则初始化为最坏情况：每个字符单独分割
        dp[i] = i  # 最多分割 i 次（每个字符都切一刀）
        # 枚举最后一个回文串的起始位置 j
        for j in range(1, i + 1):
            if is_pal[j][i]:
                # 在 j-1 和 j 之间切一刀，分割次数为 dp[j-1] + 1
                dp[i] = min(dp[i], dp[j - 1] + 1)

    return dp[n - 1]


if __name__ == "__main__":
    assert minCut("aab") == 1
    assert minCut("a") == 0
    assert minCut("ab") == 1
    assert minCut("bb") == 0
