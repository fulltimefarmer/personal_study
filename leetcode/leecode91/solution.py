"""
考点: String, Dynamic Programming
题目: Decode Ways（解码方法）
题目描述: 数字到字母的映射 A->1,...,Z->26。给定只含数字的字符串 s，计算解码方法总数。
示例: s = "12" -> 2（"AB" 或 "L"）
示例: s = "226" -> 3（"BZ", "VF", "BBF"）
示例: s = "06" -> 0
思路: 动态规划。dp[i] = (s[i-1]单独解码?dp[i-1]:0) + (两位数字解码?dp[i-2]:0)。
      空间优化为 O(1)。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def numDecodings(s: str) -> int:
    # 如果字符串以 '0' 开头，无法解码（'0' 不对应任何字母）
    if s[0] == '0':
        return 0

    # prev2 = dp[i-2], prev1 = dp[i-1]
    prev2 = 1  # 空字符串有 1 种解码方式（作为初始条件）
    prev1 = 1  # 第一个字符已确认为非 0，有 1 种解码方式

    # 从第二个字符开始计算
    for i in range(1, len(s)):
        current = 0

        # 情况一: 当前字符单独解码（1-9 都合法，0 不合法）
        if s[i] != '0':
            current += prev1

        # 情况二: 前一个字符和当前字符组成两位数解码（10-26 合法）
        # int(s[i-1:i+1]) 将 s[i-1] 到 s[i] 转为整数
        two_digit = int(s[i - 1:i + 1])
        if 10 <= two_digit <= 26:
            current += prev2

        # 滚动更新: prev2 变成之前 prev1 的值，prev1 变成当前值
        prev2, prev1 = prev1, current  # Python 同时赋值，变量先计算后更新

    return prev1


if __name__ == "__main__":
    assert numDecodings("12") == 2
    assert numDecodings("226") == 3
    assert numDecodings("06") == 0
    assert numDecodings("11106") == 2  # "AAJF" + "KJF"
    assert numDecodings("10") == 1     # "J"
