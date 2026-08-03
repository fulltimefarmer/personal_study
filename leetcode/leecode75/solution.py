"""
考点: Array, Two Pointers, Sorting
题目: Sort Colors（颜色分类）
题目描述: 给定只含 0,1,2 的数组 nums，原地排序使 0 在前、1 在中、2 在后。
示例: nums = [2,0,2,1,1,0] -> [0,0,1,1,2,2]
思路: 三指针（荷兰国旗问题）。p0 指向 0 的右边界，p2 指向 2 的左边界，curr 扫描。
      nums[curr]==0 时与 p0 交换并前进；nums[curr]==2 时与 p2 交换但不前进（需再检查）；
      nums[curr]==1 时直接前进。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def sortColors(nums: list[int]) -> None:
    """
    Do not return anything, modify nums in-place instead.
    """
    # 三指针: p0 = 下一个 0 应该放的位置, p2 = 下一个 2 应该放的位置, curr = 当前位置
    p0 = 0
    curr = 0
    p2 = len(nums) - 1

    # 当 curr 越过 p2 时，说明 2 都已经在右边排好了
    while curr <= p2:
        # Python 3.12 的 match-case 模式匹配，更清晰地处理三种情况
        match nums[curr]:
            case 0:
                # 把当前 0 换到 p0 位置，两者都前进
                # 因为从 p0 换过来的只可能是 1（0 已经排好了，2 不会在 p0 左边）
                nums[curr], nums[p0] = nums[p0], nums[curr]
                p0 += 1
                curr += 1
            case 2:
                # 把当前 2 换到 p2 位置，p2 左移
                # curr 不前进: 因为从 p2 换过来的值未知（可能是 0 或 1），需要再次检查
                nums[curr], nums[p2] = nums[p2], nums[curr]
                p2 -= 1
            case _:
                # 值为 1: 已在正确区域，直接前进
                curr += 1


if __name__ == "__main__":
    nums1 = [2, 0, 2, 1, 1, 0]
    sortColors(nums1)
    assert nums1 == [0, 0, 1, 1, 2, 2]

    nums2 = [2, 0, 1]
    sortColors(nums2)
    assert nums2 == [0, 1, 2]

    nums3 = [0]
    sortColors(nums3)
    assert nums3 == [0]
