"""
考点：双指针, 字符串, 动态规划
题目：Palindromic Substrings（回文子串）
题目描述：给定字符串 s，统计所有回文子串的数量。
思路：中心扩展法。以每个位置为中心（奇数和偶数长度），向两边扩展，遇到回文就计数。
时间复杂度：O(n²)
空间复杂度：O(1)
"""


def countSubstrings(s: str) -> int:
    n = len(s)
    count = 0

    def expand(left: int, right: int) -> None:
        """以 left 和 right 为中心向两边扩展，统计回文子串"""
        nonlocal count
        # 当左右指针都在范围内且字符相等时，找到了一个回文子串
        while left >= 0 and right < n and s[left] == s[right]:
            count += 1
            left -= 1  # 左指针向左扩展
            right += 1  # 右指针向右扩展

    for i in range(n):
        # 以单个字符为中心（奇数长度回文）：如 "aba" 以 'b' 为中心
        expand(i, i)
        # 以两个相邻字符为中心（偶数长度回文）：如 "abba" 以 'b','b' 为中心
        expand(i, i + 1)

    return count


if __name__ == "__main__":
    # 示例："abc" → 输出: 3（"a","b","c"）
    assert countSubstrings("abc") == 3
    # 示例："aaa" → 输出: 6（"a","a","a","aa","aa","aaa"）
    assert countSubstrings("aaa") == 6
