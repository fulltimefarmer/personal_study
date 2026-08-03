"""
考点：数组、二分查找
题目：Search Insert Position（搜索插入位置）
思路：标准二分查找，找到返回 mid，未找到时循环结束 left 自然指向应插入的位置
时间复杂度：O(log n)
空间复杂度：O(1)
"""
from typing import List

def searchInsert(nums: List[int], target: int) -> int:
    left, right = 0, len(nums) - 1

    while left <= right:
        mid = (left + right) >> 1  # >> 1 等价于 // 2

        if nums[mid] == target:
            return mid  # 找到目标值，直接返回索引
        elif nums[mid] < target:
            left = mid + 1  # 目标在右侧，缩小左边界
        else:
            right = mid - 1  # 目标在左侧，缩小右边界

    # 循环结束时 left > right，left 指向第一个大于 target 的位置
    # 这正是 target 应该插入的位置
    return left

if __name__ == "__main__":
    assert searchInsert([1, 3, 5, 6], 5) == 2
    assert searchInsert([1, 3, 5, 6], 2) == 1
    assert searchInsert([1, 3, 5, 6], 7) == 4
    assert searchInsert([1, 3, 5, 6], 0) == 0
    print("全部通过 ✓")
