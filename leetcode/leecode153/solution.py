"""
考点：Array, Binary Search
题目：Find Minimum in Rotated Sorted Array（寻找旋转排序数组中的最小值）
题目描述：旋转过的升序数组（无重复），找最小值，O(log n)。
示例 1：[3,4,5,1,2]，输出 1
示例 2：[4,5,6,7,0,1,2]，输出 0
示例 3：[11,13,15,17]，输出 11
思路：二分查找，比较 nums[mid] 和 nums[right]。
nums[mid] > nums[right] → 最小值在右半部分，left = mid + 1
nums[mid] < nums[right] → 最小值在左半部分（含 mid），right = mid
时间复杂度：O(log n)
空间复杂度：O(1)
"""


def findMin(nums: list[int]) -> int:
    left: int = 0
    right: int = len(nums) - 1

    while left < right:
        mid: int = (left + right) // 2  # Python 整数除法 // 等效于 Math.floor()
        if nums[mid] > nums[right]:
            # mid 处的值大于右边界，说明最小值在 mid 右边（不包含 mid）
            left = mid + 1
        else:
            # mid 处的值小于右边界，说明 mid 到 right 是递增的，最小值在 mid 或其左边
            right = mid

    # 循环结束时 left == right，指向最小值
    return nums[left]


if __name__ == "__main__":
    assert findMin([3, 4, 5, 1, 2]) == 1
    assert findMin([4, 5, 6, 7, 0, 1, 2]) == 0
    assert findMin([11, 13, 15, 17]) == 11
    assert findMin([2, 1]) == 1
