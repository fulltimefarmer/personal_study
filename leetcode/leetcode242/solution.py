"""
考点：哈希表、字符串、排序
题目：Valid Anagram（有效的字母异位词）
题目描述：判断 t 是否是 s 的字母异位词（字符出现次数相同，顺序可不同）。
  示例：s = "anagram", t = "nagaram" → true
思路：方法一——哈希表计数。用大小为 26 的数组统计 s 中每个字母的出现次数，
  遍历 t 将计数减 1，如果某个计数 < 0 则说明不是异位词。
  方法二——排序比较。Python 中排序后直接比较，简洁但 O(n log n)。
时间复杂度：O(n)
空间复杂度：O(1)（固定 26 大小）
"""

from collections import Counter


def isAnagram(s: str, t: str) -> bool:
    # 长度不同直接排除
    if len(s) != len(t):
        return False

    # 方法：Python 3.12 中可用 Counter 直接比较（ O(n) 时间 ）
    # Counter 是 dict 的子类，统计每个字符出现次数
    return Counter(s) == Counter(t)
    # 注意：Counter 相等比较会直接比较两个字典的内容


def isAnagram_v2(s: str, t: str) -> bool:
    """数组法（更轻量，适合仅有小写字母的场景）"""
    if len(s) != len(t):
        return False

    count = [0] * 26  # 26 个小写字母的计数数组
    for ch in s:
        count[ord(ch) - ord("a")] += 1  # ord 获取 ASCII 码，减去 'a' 的 ASCII 得到 0-25
    for ch in t:
        count[ord(ch) - ord("a")] -= 1
        if count[ord(ch) - ord("a")] < 0:  # t 中该字符多了一个，提前返回
            return False
    return True


if __name__ == "__main__":
    assert isAnagram("anagram", "nagaram") is True
    assert isAnagram("rat", "car") is False
    assert isAnagram("a", "ab") is False
    assert isAnagram_v2("anagram", "nagaram") is True
