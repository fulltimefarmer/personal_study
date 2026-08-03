"""
考点：数组、哈希表
题目：First Missing Positive（缺失的第一个正数）
思路：原地哈希，将数组本身当作哈希表使用，先用 n+1 替换非正数和超范围数，再将值映射到对应下标标记为负数，最后扫描找到第一个正数
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def firstMissingPositive(nums: List[int]) -> int:
    n = len(nums)

    # 第一遍：将所有非正数（≤0）和超出范围（>n）的值替换为 n+1
    # 因为缺失的最小正整数必定在 [1, n+1] 范围内
    for i in range(n):
        if nums[i] <= 0 or nums[i] > n:
            nums[i] = n + 1

    # 第二遍：将出现的数字映射到对应下标进行标记
    # 思路：如果数字 x 出现在数组中（1 ≤ x ≤ n），则把 nums[x-1] 标记为负数
    # 使用绝对值提取原值，因为该位置可能已被标记为负数
    for i in range(n):
        num = abs(nums[i])  # abs() 取绝对值，避免之前标记的负号干扰
        if num <= n:
            # 将对应下标位置的值标记为负数（如果尚未标记）
            # -abs(nums[num - 1]) 确保重复标记不会让负数变回正数
            nums[num - 1] = -abs(nums[num - 1])

    # 第三遍：扫描数组，找到第一个大于 0 的位置
    # 该位置的 index + 1 就是缺失的最小正整数
    for i in range(n):
        if nums[i] > 0:
            return i + 1

    # 所有位置都被标记（1 到 n 都出现了），返回 n+1
    return n + 1

if __name__ == "__main__":
    assert firstMissingPositive([1, 2, 0]) == 3
    assert firstMissingPositive([3, 4, -1, 1]) == 2
    assert firstMissingPositive([7, 8, 9, 11, 12]) == 1
    assert firstMissingPositive([1]) == 2
    print("全部通过 ✓")
