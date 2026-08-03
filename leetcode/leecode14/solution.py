"""
考点：字符串、字典树
题目：Longest Common Prefix（最长公共前缀）
思路：以第一个字符串为基准前缀，遍历其余字符串，不断截短前缀直到匹配
时间复杂度：O(S)，S 是所有字符串的字符总数
空间复杂度：O(1)
"""
from typing import List

def longestCommonPrefix(strs: List[str]) -> str:
    if not strs:  # Python 惯用法：空列表为 False
        return ""

    prefix = strs[0]  # 以第一个字符串作为初始前缀

    for i in range(1, len(strs)):
        # str.startswith(prefix)：检查字符串是否以 prefix 开头
        # 不匹配时不断截短 prefix 的最后一个字符
        while not strs[i].startswith(prefix):
            prefix = prefix[:-1]  # 切片到倒数第一个字符之前（去掉最后一个字符）
            if not prefix:  # 前缀变为空字符串时直接返回
                return ""

    return prefix

if __name__ == "__main__":
    assert longestCommonPrefix(["flower", "flow", "flight"]) == "fl"
    assert longestCommonPrefix(["dog", "racecar", "car"]) == ""
    assert longestCommonPrefix([""]) == ""
    print("全部通过 ✓")
