"""
考点：数组、二分查找、分治
题目：Median of Two Sorted Arrays（寻找两个正序数组的中位数）
思路：在较短数组上二分搜索分割点，使得左右两部分的最大值 <= 右部分的最小值，根据两个数组总长度的奇偶返回中位数
时间复杂度：O(log(min(m, n)))
空间复杂度：O(1)
"""
from typing import List

def findMedianSortedArrays(nums1: List[int], nums2: List[int]) -> float:
    # 确保 nums1 是较短的数组，减少二分搜索的轮数
    # 这是 O(log(min(m, n))) 复杂度的关键优化
    if len(nums1) > len(nums2):
        return findMedianSortedArrays(nums2, nums1)

    m, n = len(nums1), len(nums2)
    # total_left：两个数组左半部分应有的元素个数
    # (m + n + 1) // 2 确保奇数时左边多一个元素
    total_left = (m + n + 1) // 2

    left, right = 0, m  # 二分搜索的范围：nums1 的切割位置从 0 到 m

    while left <= right:
        # partition_a：nums1 中左半部分的元素个数
        # 使用位运算 >> 1 替代 // 2 提高效率（等价于整数除以 2）
        partition_a = (left + right) >> 1
        # partition_b：nums2 中左半部分的元素个数 = 总共需要 - nums1 中已分配的
        partition_b = total_left - partition_a

        # Python 中 float("inf") 表示正无穷大，float("-inf") 表示负无穷大
        # 边界处理：切割位置在数组边界时用 ±∞ 作为哨兵值
        max_left_a = float("-inf") if partition_a == 0 else nums1[partition_a - 1]
        min_right_a = float("inf") if partition_a == m else nums1[partition_a]
        max_left_b = float("-inf") if partition_b == 0 else nums2[partition_b - 1]
        min_right_b = float("inf") if partition_b == n else nums2[partition_b]

        # 满足条件：左半部分的最大值 <= 右半部分的最小值
        if max_left_a <= min_right_b and max_left_b <= min_right_a:
            if (m + n) % 2 == 0:  # 总长度为偶数：中位数是两个中间数的平均值
                return (max(max_left_a, max_left_b) + min(min_right_a, min_right_b)) / 2
            else:  # 总长度为奇数：中位数是左半部分的最大值
                return float(max(max_left_a, max_left_b))
        elif max_left_a > min_right_b:
            # nums1 的左半部分太大，需要将切割点左移
            right = partition_a - 1
        else:
            # nums1 的左半部分太小，需要将切割点右移
            left = partition_a + 1

    return 0.0  # 理论上不会到达这里

if __name__ == "__main__":
    assert abs(findMedianSortedArrays([1, 3], [2]) - 2.0) < 0.0001
    assert abs(findMedianSortedArrays([1, 2], [3, 4]) - 2.5) < 0.0001
    assert abs(findMedianSortedArrays([0, 0], [0, 0]) - 0.0) < 0.0001
    assert abs(findMedianSortedArrays([], [1]) - 1.0) < 0.0001
    assert abs(findMedianSortedArrays([2], []) - 2.0) < 0.0001
    print("全部通过 ✓")
