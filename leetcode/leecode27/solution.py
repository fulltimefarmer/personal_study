"""
考点：数组、双指针
题目：Remove Element（移除元素）
思路：快慢指针，快指针遍历数组，遇到不等于 val 的元素就覆盖到慢指针位置，慢指针前移
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def removeElement(nums: List[int], val: int) -> int:
    k = 0  # 慢指针：指向下一个不等于 val 的元素应该放置的位置

    # 快指针 i 从头遍历整个数组
    for i in range(len(nums)):
        if nums[i] != val:  # 遇到不等于目标值的元素
            nums[k] = nums[i]  # 将其移动到慢指针位置（原地覆盖）
            k += 1  # 慢指针前移

    return k  # k 即为新数组的长度

if __name__ == "__main__":
    nums1 = [3, 2, 2, 3]
    k1 = removeElement(nums1, 3)
    assert k1 == 2
    assert sorted(nums1[:k1]) == [2, 2]

    nums2 = [0, 1, 2, 2, 3, 0, 4, 2]
    k2 = removeElement(nums2, 2)
    assert k2 == 5
    assert sorted(nums2[:k2]) == [0, 0, 1, 3, 4]
    print("全部通过 ✓")
