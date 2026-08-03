"""
考点: Hash Table, String, Sliding Window
题目: Minimum Window Substring（最小覆盖子串）
题目描述: 给定字符串 s 和 t，返回 s 中涵盖 t 所有字符的最小子串。不存在则返回 ""。
示例: s = "ADOBECODEBANC", t = "ABC" -> "BANC"
思路: 滑动窗口 + 哈希表。右指针扩展窗口，满足条件后左指针收缩，
      用 need map 记录字符需求，valid 计数已满足的字符种类。
时间复杂度: O(n)
空间复杂度: O(|Sigma|)  Sigma 为字符集大小
"""

from collections import defaultdict


def minWindow(s: str, t: str) -> str:
    # need: 记录 t 中每个字符的需求数量
    need: dict[str, int] = defaultdict(int)
    for char in t:
        need[char] += 1

    # window: 记录当前窗口中包含的来自 t 的字符数量
    window: dict[str, int] = defaultdict(int)
    left = 0
    valid = 0  # 已满足的字符种类数（当 window[c] == need[c] 时 +1）
    start = 0  # 最小覆盖子串的起始索引
    min_len = float('inf')  # 最小长度，初始设为无穷大

    # right 指针向右扩展窗口
    for right, c in enumerate(s):
        # -- 扩大窗口 --
        if c in need:
            window[c] += 1
            # 当某个字符在窗口中的数量刚好满足需求时，valid 计数加一
            if window[c] == need[c]:
                valid += 1

        # -- 收缩窗口 --
        # 当所有需求字符都已满足时，尝试从左边收缩以找到最小子串
        # len(need) 获取 need dict 的键数量，即 t 中不同字符的种类数
        while valid == len(need):
            # 更新最小子串
            if right - left + 1 < min_len:
                start = left
                min_len = right - left + 1

            # 左指针右移，移除 s[left]
            d = s[left]
            left += 1

            if d in need:
                # 如果移除前 window[d] 刚好满足 need[d]，移除后就不再满足
                if window[d] == need[d]:
                    valid -= 1
                window[d] -= 1  # 无论是否减到 need 以下，窗口数量都要减

    # 三元表达式: 如果 min_len 还是无穷大，说明没找到，返回空字符串
    return "" if min_len == float('inf') else s[start:start + min_len]


if __name__ == "__main__":
    assert minWindow("ADOBECODEBANC", "ABC") == "BANC"
    assert minWindow("a", "a") == "a"
    assert minWindow("a", "aa") == ""
    assert minWindow("aa", "aa") == "aa"
    assert minWindow("ab", "b") == "b"
