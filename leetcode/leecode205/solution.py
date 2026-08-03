"""
考点：哈希表、字符串
题目：Isomorphic Strings（同构字符串）
思路：维护两个映射表 s→t 和 t→s，遍历检查双向映射是否一致。
时间复杂度：O(n)
空间复杂度：O(1)（ASCII 字符集 256）
"""


def isIsomorphic(s: str, t: str) -> bool:
    # 用长度为 256 的列表模拟字符映射表（ASCII 范围）
    # ord() 获取字符的 ASCII 码作为索引
    map_st: list[int] = [0] * 256  # s 到 t 的映射
    map_ts: list[int] = [0] * 256  # t 到 s 的映射

    for c1, c2 in zip(s, t):  # zip() 同时迭代两个字符串的对应字符
        i1, i2 = ord(c1), ord(c2)
        # 两个方向都未映射过，建立双向映射
        if map_st[i1] == 0 and map_ts[i2] == 0:
            map_st[i1] = i2   # 存 ASCII 码值（非 0 即可）
            map_ts[i2] = i1
        # 检查双向映射是否一致
        elif map_st[i1] != i2 or map_ts[i2] != i1:
            return False

    return True


if __name__ == "__main__":
    # s="egg", t="add" → true
    assert isIsomorphic("egg", "add") is True
    # s="foo", t="bar" → false
    assert isIsomorphic("foo", "bar") is False
    # s="paper", t="title" → true
    assert isIsomorphic("paper", "title") is True
    print("全部测试通过")
