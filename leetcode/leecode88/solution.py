"""
考点: Array, Two Pointers, Sorting
题目: Merge Sorted Array（合并两个有序数组）
题目描述: 两个非递减数组 nums1(m 个有效元素) 和 nums2(n 个)，合并到 nums1 中保持非递减。
      nums1 的长度为 m+n，后 n 位为 0 占位。
示例: nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3 -> [1,2,2,3,5,6]
思路: 双指针从后向前。p1=m-1, p2=n-1, p=m+n-1，较大值填入末尾。
      从后向前避免覆盖 nums1 中未处理的元素。
时间复杂度: O(m + n)
空间复杂度: O(1)
"""


def merge(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    """
    Do not return anything, modify nums1 in-place instead.
    """
    # 三个指针从数组末尾开始
    p1 = m - 1      # nums1 有效元素的末尾
    p2 = n - 1      # nums2 的末尾
    p = m + n - 1   # 合并后数组的末尾位置

    # 只需要确保 nums2 元素全部放入即可
    # 当 p2 < 0 时 nums2 为空, nums1 剩余元素已在正确位置
    while p2 >= 0:
        # 选择 nums1 当前元素 vs nums2 当前元素中较大的填入末尾
        # p1 >= 0 确保 nums1 还有未比较的元素
        if p1 >= 0 and nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1


if __name__ == "__main__":
    nums1_1 = [1, 2, 3, 0, 0, 0]
    merge(nums1_1, 3, [2, 5, 6], 3)
    assert nums1_1 == [1, 2, 2, 3, 5, 6]

    nums1_2 = [1]
    merge(nums1_2, 1, [], 0)
    assert nums1_2 == [1]

    nums1_3 = [0]
    merge(nums1_3, 0, [1], 1)
    assert nums1_3 == [1]
