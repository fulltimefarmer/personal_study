"""
考点：数组、双指针
题目：Next Permutation（下一个排列）
思路：从右向左找第一个升序对，找到后在右侧找刚好大于该值的元素交换，再将右侧反转使其变为最小排列
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def nextPermutation(nums: List[int]) -> None:
    """
    原地修改 nums，不返回任何值（LeetCode 要求）
    算法步骤：
    1. 从右向左找到第一个相邻升序对 nums[i] < nums[i+1]
    2. 在 i 右侧找到刚好大于 nums[i] 的最小值 nums[j]
    3. 交换 nums[i] 和 nums[j]
    4. 反转 i+1 到末尾使其变为升序（最小排列）
    """
    n = len(nums)
    # 步骤 1：从倒数第二个元素向左扫描
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1

    # 如果找到了升序对（即 i >= 0），说明存在更大的排列
    if i >= 0:
        # 步骤 2：在 i 右侧找到刚好大于 nums[i] 的最小值
        # 由于右侧是降序的，从右向左找第一个大于 nums[i] 的值即可
        j = n - 1
        while j >= 0 and nums[j] <= nums[i]:
            j -= 1
        # 步骤 3：Python 元组交换（tuple unpacking），无需临时变量
        nums[i], nums[j] = nums[j], nums[i]

    # 步骤 4：反转 i+1 到末尾，使其变为升序（最小排列）
    left, right = i + 1, n - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1

if __name__ == "__main__":
    nums1 = [1, 2, 3]
    nextPermutation(nums1)
    assert nums1 == [1, 3, 2]

    nums2 = [3, 2, 1]
    nextPermutation(nums2)
    assert nums2 == [1, 2, 3]

    nums3 = [1, 1, 5]
    nextPermutation(nums3)
    assert nums3 == [1, 5, 1]
    print("全部通过 ✓")
