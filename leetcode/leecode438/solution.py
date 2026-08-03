"""
考点：哈希表、字符串、滑动窗口
题目：Find All Anagrams in a String（找到字符串中所有字母异位词）—— LeetCode 438
题目描述：在 s 中找出所有 p 的字母异位词的起始索引
思路：固定大小滑动窗口 + 计数数组。维护两个 26 长数组分别统计 p 和窗口。
      滑动比较，相等则记录起始索引。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def findAnagrams(s: str, p: str) -> list[int]:
    result: list[int] = []
    if len(p) > len(s):
        return result  # p 比 s 长，不可能匹配

    # 两个长度为 26 的计数数组，分别统计 p 和 s 窗口的字符频率
    target: list[int] = [0] * 26
    window: list[int] = [0] * 26

    # ord('a') 作为基准偏移量
    base = ord("a")

    # 初始化：统计 p 和 s 的前 len(p) 个字符
    for i in range(len(p)):
        target[ord(p[i]) - base] += 1
        window[ord(s[i]) - base] += 1

    # 定义辅助函数判断两个计数数组是否相等
    def matches() -> bool:
        return target == window

    # 检查初始窗口
    if matches():
        result.append(0)

    # 滑动窗口：i 为窗口的右边界（新加入的字符）
    for i in range(len(p), len(s)):
        # 窗口右移：加入 s[i]
        window[ord(s[i]) - base] += 1
        # 移除窗口最左侧字符 s[i - len(p)]
        window[ord(s[i - len(p)]) - base] -= 1

        if matches():
            # 窗口起始索引为 i - len(p) + 1
            result.append(i - len(p) + 1)

    return result


if __name__ == "__main__":
    assert findAnagrams("cbaebabacd", "abc") == [0, 6]
    assert findAnagrams("abab", "ab") == [0, 1, 2]
    assert findAnagrams("a", "ab") == []
    assert findAnagrams("abc", "d") == []
    assert findAnagrams("baa", "aa") == [1]
    print("所有断言通过！")
