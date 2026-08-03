"""
考点：双指针、字符串、动态规划
题目：Is Subsequence（判断子序列）—— LeetCode 392
题目描述：判断 s 是否为 t 的子序列（删除 t 中若干字符得到 s）
思路：双指针。i 指向 s，j 指向 t，匹配时 i++，j 始终前进。
      最终若 i == len(s) 则为子序列。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def isSubsequence(s: str, t: str) -> bool:
    # 双指针：i 遍历 s，j 遍历 t
    i = j = 0

    while i < len(s) and j < len(t):
        # 如果当前字符匹配，s 的指针前进
        if s[i] == t[j]:
            i += 1
        # t 的指针始终前进，不管是否匹配
        j += 1

    # 如果 s 的所有字符都在 t 中按顺序找到，则 i == len(s)
    return i == len(s)


if __name__ == "__main__":
    assert isSubsequence("abc", "ahbgdc") is True
    assert isSubsequence("axc", "ahbgdc") is False
    assert isSubsequence("", "ahbgdc") is True  # 空字符串是任何字符串的子序列
    assert isSubsequence("abc", "") is False
    assert isSubsequence("aaaa", "bbaaaa") is True
    print("所有断言通过！")
