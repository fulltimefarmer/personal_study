"""
考点：哈希表、字符串、排序
题目：Valid Anagram（有效的字母异位词）
思路：26 位计数数组，s 的字符 +1，t 的字符 -1，最后检查是否全为 0。
      进阶（Unicode）：用 dict 代替数组。
时间复杂度：O(n)
空间复杂度：O(1)（固定 26 个字母）
"""


def isAnagram(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False  # 长度不同一定不是异位词

    # 用长度为 26 的数组统计字符出现次数
    # ord(ch) - 97 将 'a'-'z' 映射到 0-25
    count = [0] * 26

    for i in range(len(s)):
        count[ord(s[i]) - 97] += 1  # s 中的字符 +1
        count[ord(t[i]) - 97] -= 1  # t 中的字符 -1

    # 如果所有计数都是 0，说明两个字符串字符频次完全一致
    return all(c == 0 for c in count)


if __name__ == "__main__":
    # 示例 1: s="anagram", t="nagaram" → true
    assert isAnagram("anagram", "nagaram") is True
    # 示例 2: s="rat", t="car" → false
    assert isAnagram("rat", "car") is False
    print("全部测试通过")
