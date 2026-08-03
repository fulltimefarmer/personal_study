"""
考点：字符串、双指针
题目：Find the Index of the First Occurrence in a String（找出字符串中第一个匹配项的下标）
思路：滑动窗口法，遍历 haystack 中每个可能的起始位置，检查从该位置开始的子串是否匹配 needle
时间复杂度：O(n * m)
空间复杂度：O(1)
"""

def strStr(haystack: str, needle: str) -> int:
    n, m = len(haystack), len(needle)

    if m == 0:
        return 0  # 空 needle 约定返回 0

    # 遍历 haystack 中每个可能的起始位置
    # range 的上限为 n - m，确保剩余字符足够匹配 needle
    for i in range(n - m + 1):
        # 切片比较：haystack[i:i+m] 取从 i 开始长度为 m 的子串
        # 直接与 needle 比较，Python 字符串比较是逐字符的
        if haystack[i : i + m] == needle:
            return i  # 第一个匹配项的下标

    return -1  # 未找到

if __name__ == "__main__":
    assert strStr("sadbutsad", "sad") == 0
    assert strStr("leetcode", "leeto") == -1
    assert strStr("hello", "ll") == 2
    assert strStr("aaaaa", "bba") == -1
    assert strStr("", "") == 0
    print("全部通过 ✓")
