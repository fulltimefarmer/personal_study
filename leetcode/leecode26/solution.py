"""
考点：数组、双指针
题目：Remove Duplicates from Sorted Array（删除有序数组中的重复项）
思路：快慢指针，慢指针 k 指向已去重数组末尾，快指针 i 遍历数组，遇到不同元素时覆盖到慢指针的下一个位置
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def removeDuplicates(nums: List[int]) -> int:
    if not nums:  # 空数组直接返回 0
        return 0

    k = 0  # 慢指针：指向已去重部分的最后一个元素的下标

    # 快指针 i 从 1 开始遍历
    for i in range(1, len(nums)):
        # 当快指针遇到与慢指针不同的元素时，扩展已去重部分
        if nums[i] != nums[k]:
            k += 1  # 慢指针前移
            nums[k] = nums[i]  # 将新元素覆盖到慢指针位置

    return k + 1  # 长度为下标 + 1

if __name__ == "__main__":
    nums1 = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    k1 = removeDuplicates(nums1)
    assert k1 == 5
    assert nums1[:k1] == [0, 1, 2, 3, 4]

    nums2 = [1, 1, 2]
    k2 = removeDuplicates(nums2)
    assert k2 == 2
    assert nums2[:k2] == [1, 2]
    print("全部通过 ✓")
