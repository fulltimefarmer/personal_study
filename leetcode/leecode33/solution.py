"""
考点：数组、二分查找
题目：Search in Rotated Sorted Array（搜索旋转排序数组）
思路：二分查找，每次判断 mid 落在左半有序区间还是右半有序区间，据此确定 target 在哪个区间并调整搜索边界
时间复杂度：O(log n)
空间复杂度：O(1)
"""
from typing import List

def search(nums: List[int], target: int) -> int:
    left, right = 0, len(nums) - 1

    while left <= right:
        # >> 1 是位运算，等价于 // 2，但效率更高
        mid = (left + right) >> 1

        if nums[mid] == target:
            return mid  # 找到目标直接返回

        # 关键判断：mid 落在哪个有序区间？
        if nums[left] <= nums[mid]:
            # 左半部分 [left, mid] 是有序的（非递减）
            # 判断 target 是否在这个有序区间内
            if nums[left] <= target < nums[mid]:
                right = mid - 1  # target 在左半部分，缩小右边界
            else:
                left = mid + 1  # target 在右半部分，缩小左边界
        else:
            # 右半部分 [mid, right] 是有序的
            # 判断 target 是否在这个有序区间内
            if nums[mid] < target <= nums[right]:
                left = mid + 1  # target 在右半部分，缩小左边界
            else:
                right = mid - 1  # target 在左半部分，缩小右边界

    return -1  # 未找到

if __name__ == "__main__":
    assert search([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search([1], 0) == -1
    assert search([1], 1) == 0
    assert search([3, 1], 1) == 1
    print("全部通过 ✓")
