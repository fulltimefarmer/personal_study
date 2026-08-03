"""
考点：哈希表、字符串、滑动窗口
题目：Longest Substring Without Repeating Characters（无重复字符的最长子串）
思路：滑动窗口 + 哈希表，维护左右指针，哈希表记录字符最近出现位置，遇到重复时左指针跳到重复位置的下一位
时间复杂度：O(n)
空间复杂度：O(min(n, 字符集大小))
"""

def lengthOfLongestSubstring(s: str) -> int:
    # 哈希表：字符 -> 最近一次出现的位置索引
    # 使用字典实现，O(1) 查找和更新
    char_pos: dict[str, int] = {}
    left = 0  # 滑动窗口的左边界（包含）
    max_len = 0  # 记录最长无重复子串的长度

    for right, ch in enumerate(s):  # enumerate 同时获取索引和字符值
        # 关键判断：字符已存在 且 其位置在窗口范围内
        # 两个条件缺一不可：如果重复位置在 left 左边说明已不在当前窗口中，可忽略
        if ch in char_pos and char_pos[ch] >= left:
            # 将左指针跳到重复字符之后，跳过重复部分
            left = char_pos[ch] + 1

        char_pos[ch] = right  # 更新字符的最新出现位置
        # 计算当前窗口长度：right - left + 1
        max_len = max(max_len, right - left + 1)

    return max_len

if __name__ == "__main__":
    assert lengthOfLongestSubstring("abcabcbb") == 3  # "abc"
    assert lengthOfLongestSubstring("bbbbb") == 1     # "b"
    assert lengthOfLongestSubstring("pwwkew") == 3    # "wke"
    assert lengthOfLongestSubstring("") == 0
    assert lengthOfLongestSubstring(" ") == 1
    print("全部通过 ✓")
