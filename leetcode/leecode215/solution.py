"""
考点：数组、分治、快速选择（Quickselect）、排序、堆
题目：Kth Largest Element in an Array（数组中的第 K 个最大元素）
思路：快速选择。三路分区——大于/等于/小于 pivot，根据各部分长度决定在哪一部分继续查找。
      第 k 大 = 第 n-k 小（从 0 开始），因此 targetIdx = n - k。
时间复杂度：平均 O(n)，最坏 O(n²)
空间复杂度：O(log n)（递归栈）
"""

import random


def findKthLargest(nums: list[int], k: int) -> int:
    n = len(nums)
    target_idx = n - k  # 第 k 大对应的排序后下标

    def quick_select(left: int, right: int) -> int:
        if left == right:
            return nums[left]  # 区间只有一个元素

        # 随机选取 pivot，避免最坏情况
        pivot_idx = random.randint(left, right)
        pivot = nums[pivot_idx]

        # 三路分区（荷兰国旗问题）：
        # lt 为小于区右边界，gt 为大于区左边界，i 为当前扫描位置
        lt = left
        gt = right
        i = left

        while i <= gt:
            if nums[i] < pivot:
                # 小于 pivot，交换到小于区
                nums[lt], nums[i] = nums[i], nums[lt]
                lt += 1
                i += 1
            elif nums[i] > pivot:
                # 大于 pivot，交换到大于区
                nums[gt], nums[i] = nums[i], nums[gt]
                gt -= 1  # 注意：交换后 i 不动，因为换过来的元素还需判断
            else:
                # 等于 pivot，直接跳过
                i += 1

        # 分区后：[left, lt-1] < pivot, [lt, gt] == pivot, [gt+1, right] > pivot
        if target_idx < lt:
            return quick_select(left, lt - 1)
        elif target_idx > gt:
            return quick_select(gt + 1, right)
        else:
            # target_idx 在等于 pivot 的区域内
            return nums[target_idx]

    return quick_select(0, n - 1)


if __name__ == "__main__":
    # 示例 1: [3,2,1,5,6,4], k=2 → 5
    assert findKthLargest([3, 2, 1, 5, 6, 4], 2) == 5
    # 示例 2: [3,2,3,1,2,4,5,5,6], k=4 → 4
    assert findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    print("全部测试通过")
