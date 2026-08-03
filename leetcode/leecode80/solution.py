"""
考点: Array, Two Pointers
题目: Remove Duplicates from Sorted Array II（删除有序数组中的重复项 II）
题目描述: 原地删除有序数组中的重复项，使每个元素最多出现两次，返回新长度。
示例: nums = [1,1,1,2,2,3] -> 5, nums = [1,1,2,2,3]
示例: nums = [0,0,1,1,1,1,2,3,3] -> 7, nums = [0,0,1,1,2,3,3]
思路: 双指针。slow 指向写入位置，count 记录当前数字的出现次数。
      只有 count <= 2 时才写入，超过两次跳过。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def removeDuplicates(nums: list[int]) -> int:
    if len(nums) <= 2:
        return len(nums)

    # slow: 下一个可以写入的位置
    slow = 1
    # count: 当前连续数字的出现次数（至少为 1）
    count = 1

    # 从第二个元素开始遍历
    for i in range(1, len(nums)):
        # 与前一元素比较更新 count
        if nums[i] == nums[i - 1]:
            count += 1
        else:
            count = 1  # 新数字，计数器重置

        # 只有出现次数 <= 2 时才保留
        if count <= 2:
            nums[slow] = nums[i]  # 原地覆盖
            slow += 1

    return slow  # 返回新数组的有效长度


if __name__ == "__main__":
    nums1 = [1, 1, 1, 2, 2, 3]
    k1 = removeDuplicates(nums1)
    assert k1 == 5
    assert nums1[:k1] == [1, 1, 2, 2, 3]

    nums2 = [0, 0, 1, 1, 1, 1, 2, 3, 3]
    k2 = removeDuplicates(nums2)
    assert k2 == 7
    assert nums2[:k2] == [0, 0, 1, 1, 2, 3, 3]

    nums3 = [1, 2, 2, 2]
    k3 = removeDuplicates(nums3)
    assert k3 == 3
    assert nums3[:k3] == [1, 2, 2]
