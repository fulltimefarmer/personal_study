"""
考点：数组、双指针、二分查找
题目：Two Sum II - Input Array Is Sorted（两数之和 II - 输入有序数组）
题目描述：在已排序数组中找到和为 target 的两个数，返回其下标（从 1 开始）。
  示例：numbers = [2,7,11,15], target = 9 → [1,2]
思路：双指针。left 指向开头，right 指向末尾。
  sum < target → left++（需要更大的和）
  sum > target → right--（需要更小的和）
时间复杂度：O(n)
空间复杂度：O(1)
"""


def twoSum(numbers: list[int], target: int) -> list[int]:
    # left 从数组开头开始，right 从数组末尾开始
    left = 0
    right = len(numbers) - 1

    while left < right:  # 题目保证有解，left 和 right 不能重叠
        s = numbers[left] + numbers[right]  # 当前两数之和
        if s == target:
            return [left + 1, right + 1]  # 题目要求下标从 1 开始，所以各 +1
        elif s < target:
            left += 1  # 和太小，left 右移使和变大（数组已排序）
        else:
            right -= 1  # 和太大，right 左移使和变小（数组已排序）

    return []  # 题目保证有解，此行仅满足类型检查


if __name__ == "__main__":
    assert twoSum([2, 7, 11, 15], 9) == [1, 2]
    assert twoSum([2, 3, 4], 6) == [1, 3]
    assert twoSum([-1, 0], -1) == [1, 2]
