"""
考点：栈, 贪心, 数组, 双指针, 排序, 单调栈
题目：Shortest Unsorted Continuous Subarray（最短无序连续子数组）
题目描述：给定 nums，找出最短的连续子数组，排序后整个数组变为升序。返回子数组长度。
思路：一次遍历。从左到右找右边界（遇到比当前最大值小的数字时更新 right），从右到左找左边界（遇到比当前最小值大的数字时更新 left）。right-left+1 即为结果。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def findUnsortedSubarray(nums: list[int]) -> int:
    n = len(nums)
    # float("inf") 表示正无穷大，用于初始最小值；负无穷大用于初始最大值
    max_val = float("-inf")  # 从左往右遍历时的当前最大值
    min_val = float("inf")  # 从右往左遍历时的当前最小值
    left = -1
    right = -1

    # 从左往右找右边界：如果遇到比当前最大值小的元素，说明它不在正确位置，更新 right
    for i, num in enumerate(nums):
        if num < max_val:
            right = i  # 当前元素比之前最大值小，说明需要被排序，更新右边界
        else:
            max_val = num  # 更新左侧已遍历部分的最大值

    # 从右往左找左边界：如果遇到比当前最小值大的元素，说明它不在正确位置，更新 left
    for i in range(n - 1, -1, -1):
        if nums[i] > min_val:
            left = i  # 当前元素比之后最小值大，说明需要被排序，更新左边界
        else:
            min_val = nums[i]  # 更新右侧已遍历部分的最小值

    # 如果数组已经有序，right <= left，返回 0
    return 0 if right <= left else right - left + 1


if __name__ == "__main__":
    # 示例：[2,6,4,8,10,9,15] → 输出: 5（子数组 [6,4,8,10,9]）
    assert findUnsortedSubarray([2, 6, 4, 8, 10, 9, 15]) == 5
    # 示例：[1,2,3,4] → 输出: 0
    assert findUnsortedSubarray([1, 2, 3, 4]) == 0
    # 示例：[1] → 输出: 0
    assert findUnsortedSubarray([1]) == 0
