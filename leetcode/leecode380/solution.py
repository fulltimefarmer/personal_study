"""
考点：设计、数组、哈希表、随机化
题目：Insert Delete GetRandom O(1)（O(1)时间插入删除和获取随机元素）—— LeetCode 380
题目描述：设计数据结构支持 O(1) 插入、删除、随机获取元素
思路：HashMap 存值→索引 + 数组存值。删除时将被删元素与末尾交换后 pop，
      实现 O(1) 删除。getRandom 直接从数组随机索引。
时间复杂度：O(1) 各操作
空间复杂度：O(n)
"""

import random


class RandomizedSet:
    """
    O(1) 时间插入、删除、随机获取元素的集合。
    核心技巧：用列表存值，用字典存值到列表索引的映射。
    删除时把待删元素与列表末尾交换再 pop，实现 O(1)。
    """

    def __init__(self) -> None:
        # dict[int, int]：值 → 在列表中的索引
        self.val_to_index: dict[int, int] = {}
        # list[int]：实际存储值的数组
        self.values: list[int] = []

    def insert(self, val: int) -> bool:
        # 集合中已存在该值，插入失败
        if val in self.val_to_index:
            return False
        # 将值加入列表末尾，并记录索引映射
        self.val_to_index[val] = len(self.values)
        self.values.append(val)
        return True

    def remove(self, val: int) -> bool:
        # 集合中不存在该值，删除失败
        if val not in self.val_to_index:
            return False

        # O(1) 删除技巧：将待删元素与列表最后一个元素交换，然后 pop
        index = self.val_to_index[val]  # 待删元素在列表中的索引
        last_val = self.values[-1]      # 列表最后一个元素

        # 将最后一个元素移到待删元素的位置（覆盖删除）
        self.values[index] = last_val
        self.val_to_index[last_val] = index  # 更新映射

        # 删除列表末尾和字典中的待删元素
        self.values.pop()
        del self.val_to_index[val]

        return True

    def getRandom(self) -> int:
        # random.choice(seq)：从非空序列中随机返回一个元素
        # 等效于 self.values[random.randrange(len(self.values))]
        return random.choice(self.values)


if __name__ == "__main__":
    rs = RandomizedSet()
    assert rs.insert(1) is True   # 插入 1 成功
    assert rs.remove(2) is False  # 不存在 2
    assert rs.insert(2) is True   # 插入 2 成功
    assert rs.insert(1) is False  # 1 已存在

    val = rs.getRandom()
    assert val in (1, 2)  # 随机返回 1 或 2

    assert rs.remove(1) is True
    assert rs.insert(2) is False  # 2 已存在
    assert rs.getRandom() == 2    # 只剩 2

    print("所有断言通过！")
