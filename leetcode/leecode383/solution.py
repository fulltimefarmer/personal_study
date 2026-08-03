"""
考点：哈希表、字符串、计数
题目：Ransom Note（赎金信）—— LeetCode 383
题目描述：判断 ransomNote 能否由 magazine 中的字符构成（每个字符只能用一次）
思路：用长度 26 的数组统计 magazine 字符频率，
      遍历 ransomNote 逐个扣减，出现负数即返回 false。
时间复杂度：O(m + n)
空间复杂度：O(1)
"""

def canConstruct(ransomNote: str, magazine: str) -> bool:
    # Python 中 ord('a') 返回字符 'a' 的 ASCII/Unicode 码点值 97
    # 用 ord(ch) - ord('a') 将 'a'~'z' 映射到 0~25
    count: list[int] = [0] * 26

    # 第一遍遍历：统计 magazine 中每个字母的出现次数
    for ch in magazine:
        count[ord(ch) - ord("a")] += 1

    # 第二遍遍历：检查 ransomNote 的每个字符是否可用
    for ch in ransomNote:
        idx = ord(ch) - ord("a")
        count[idx] -= 1
        # 如果出现负数，说明 magazine 中该字符不够用
        if count[idx] < 0:
            return False

    return True


if __name__ == "__main__":
    assert canConstruct("a", "b") is False
    assert canConstruct("aa", "ab") is False
    assert canConstruct("aa", "aab") is True
    assert canConstruct("", "") is True
    assert canConstruct("abc", "cba") is True
    assert canConstruct("a" * 100, "a" * 99) is False
    print("所有断言通过！")
