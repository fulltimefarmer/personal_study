"""
考点：数组、分治、快速选择、堆
题目：Kth Largest Element in an Array（数组中的第K个最大元素）
题目描述：找出数组中第 k 大的元素（注意是排序后的第 k 大，不是第 k 小）。
  示例：nums = [3,2,1,5,6,4], k = 2 → 5
思路：快速选择算法（QuickSelect）。类似快排，每次选 pivot 分区。
  如果 pivot 位置正好是 len - k（第 k 大的索引），则返回；否则递归左侧或右侧。
  平均 O(n)，最坏 O(n²)。也可用大小为 k 的小顶堆。
时间复杂度：O(n) 平均，O(n²) 最坏
空间复杂度：O(1)（迭代版本）
"""

import random


def findKthLargest(nums: list[int], k: int) -> int:
    # 第 k 大元素 = 排序后索引为 len(nums) - k 的元素
    target = len(nums) - k

    def quick_select(left: int, right: int) -> int:
        # 随机选取 pivot 并交换到最右边，避免最坏情况
        pivot_idx = random.randint(left, right)
        nums[pivot_idx], nums[right] = nums[right], nums[pivot_idx]
        pivot = nums[right]

        # 分区：将小于 pivot 的放左边，大于 pivot 的放右边
        i = left  # i 指向下一个小于 pivot 的元素应该放的位置
        for j in range(left, right):
            if nums[j] < pivot:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
        # 将 pivot 放到正确位置
        nums[i], nums[right] = nums[right], nums[i]

        # i 就是 pivot 的最终位置
        match i:
            case _ if i == target:
                return nums[i]  # 找到目标
            case _ if i < target:
                return quick_select(i + 1, right)  # 目标在右侧，递归右半部分
            case _:
                return quick_select(left, i - 1)  # 目标在左侧，递归左半部分

    return quick_select(0, len(nums) - 1)


if __name__ == "__main__":
    assert findKthLargest([3, 2, 1, 5, 6, 4], 2) == 5
    assert findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert findKthLargest([1], 1) == 1
