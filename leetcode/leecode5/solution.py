"""
考点：字符串、动态规划、双指针
题目：Longest Palindromic Substring（最长回文子串）
思路：中心扩展法，对每个位置分别以单字符（奇数长度）和双字符（偶数长度）为中心向两侧扩展，记录最长回文子串
时间复杂度：O(n^2)
空间复杂度：O(1)
"""

def longestPalindrome(s: str) -> str:
    if len(s) < 2:
        return s

    start = 0  # 最长回文子串的起始索引
    max_len = 1  # 最长回文子串的长度，初始为 1（单字符一定是回文）

    # 内嵌函数：以 left 和 right 为中心向两边扩展
    # Python 中内嵌函数可直接访问外层作用域的变量（如 start, max_len）
    def expandAroundCenter(left: int, right: int) -> None:
        # 使用 nonlocal 声明：告诉 Python 我们要修改外层函数的变量而非创建局部变量
        # 没有 nonlocal，在嵌套函数中对 start/max_len 的赋值会创建新的局部变量
        nonlocal start, max_len
        while left >= 0 and right < len(s) and s[left] == s[right]:
            cur_len = right - left + 1
            if cur_len > max_len:
                max_len = cur_len
                start = left
            left -= 1  # 向左扩展
            right += 1  # 向右扩展

    # 遍历每个位置作为中心点
    for i in range(len(s)):
        expandAroundCenter(i, i)  # 奇数长度回文中心：单字符
        expandAroundCenter(i, i + 1)  # 偶数长度回文中心：两个相邻字符

    # 切片（slice）：s[start:start + max_len] 取子串，左闭右开区间
    return s[start:start + max_len]

if __name__ == "__main__":
    result = longestPalindrome("babad")
    assert result in ("bab", "aba")  # "bab" 和 "aba" 都正确
    assert longestPalindrome("cbbd") == "bb"
    assert longestPalindrome("a") == "a"
    print("全部通过 ✓")
