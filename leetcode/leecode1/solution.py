"""
考点：哈希表、数组
题目：Two Sum（两数之和）
思路：使用哈希表存储已遍历元素的值和下标，对于每个元素检查 target - num 是否已在表中
时间复杂度：O(n)
空间复杂度：O(n)
"""
from typing import List

def twoSum(nums: List[int], target: int) -> List[int]:
    # 创建哈希表：值 -> 下标，利用 Python 字典 O(1) 查找
    seen: dict[int, int] = {}
    for i, num in enumerate(nums):  # enumerate 同时获取索引和值
        complement = target - num
        if complement in seen:  # 字典的 in 操作时间复杂度为 O(1)
            return [seen[complement], i]
        seen[num] = i
    return []

if __name__ == "__main__":
    assert twoSum([2, 7, 11, 15], 9) == [0, 1]
    assert twoSum([3, 2, 4], 6) == [1, 2]
    assert twoSum([3, 3], 6) == [0, 1]
    print("全部通过 ✓")
