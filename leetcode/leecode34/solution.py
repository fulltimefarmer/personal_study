"""
考点：数组、二分查找
题目：Find First and Last Position of Element in Sorted Array（在排序数组中查找元素的第一个和最后一个位置）
思路：两次二分查找，分别找起始位置（找到 target 后继续向左缩）和结束位置（找到 target 后继续向右缩）
时间复杂度：O(log n)
空间复杂度：O(1)
"""
from typing import List

def searchRange(nums: List[int], target: int) -> List[int]:
    def findFirst() -> int:
        """二分查找 target 的第一次出现位置"""
        left, right = 0, len(nums) - 1
        result = -1

        while left <= right:
            mid = (left + right) >> 1  # 位运算等价于 // 2
            if nums[mid] == target:
                result = mid  # 记录当前位置
                right = mid - 1  # 继续向左搜索，看有无更早的出现
            elif nums[mid] < target:
                left = mid + 1  # 中间值偏小，target 在右侧
            else:
                right = mid - 1  # 中间值偏大，target 在左侧

        return result

    def findLast() -> int:
        """二分查找 target 的最后一次出现位置"""
        left, right = 0, len(nums) - 1
        result = -1

        while left <= right:
            mid = (left + right) >> 1
            if nums[mid] == target:
                result = mid  # 记录当前位置
                left = mid + 1  # 继续向右搜索，看有无更晚的出现
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1

        return result

    return [findFirst(), findLast()]

if __name__ == "__main__":
    assert searchRange([5, 7, 7, 8, 8, 10], 8) == [3, 4]
    assert searchRange([5, 7, 7, 8, 8, 10], 6) == [-1, -1]
    assert searchRange([], 0) == [-1, -1]
    assert searchRange([1], 1) == [0, 0]
    print("全部通过 ✓")
