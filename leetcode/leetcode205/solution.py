"""
考点：哈希表、字符串
题目：Isomorphic Strings（同构字符串）
题目描述：判断 s 和 t 是否同构，即 s 中每个字符可以唯一映射到 t 中每个字符，并且顺序保持。
  示例：s = "egg", t = "add" → true；s = "foo", t = "bar" → false
思路：双映射。用两个字典分别记录 s→t 和 t→s 的映射关系。
  如果当前字符对不在映射中则添加，如果已存在但映射不匹配则返回 False。
时间复杂度：O(n)
空间复杂度：O(1)（字符集有限，最多 256 个）
"""


def isIsomorphic(s: str, t: str) -> bool:
    s_to_t: dict[str, str] = {}  # s 中字符 → t 中字符的映射
    t_to_s: dict[str, str] = {}  # t 中字符 → s 中字符的映射（反向映射保证一对一）

    for ch_s, ch_t in zip(s, t):  # zip 同时遍历两个字符串
        if ch_s in s_to_t:
            if s_to_t[ch_s] != ch_t:  # s 中字符之前映射的不是当前 t 字符，不同构
                return False
        else:
            s_to_t[ch_s] = ch_t

        if ch_t in t_to_s:
            if t_to_s[ch_t] != ch_s:  # t 中字符之前映射的不是当前 s 字符，不同构
                return False
        else:
            t_to_s[ch_t] = ch_s

    return True


if __name__ == "__main__":
    assert isIsomorphic("egg", "add") is True
    assert isIsomorphic("foo", "bar") is False
    assert isIsomorphic("paper", "title") is True
    assert isIsomorphic("badc", "baba") is False
