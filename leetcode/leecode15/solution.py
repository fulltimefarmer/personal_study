"""
考点：数组、双指针、排序
题目：3Sum（三数之和）
思路：排序后固定第一个数，使用双指针在剩余区间寻找另外两个数和为 -nums[i]，跳过重复值以避免重复三元组
时间复杂度：O(n^2)
空间复杂度：O(1)（不计结果数组）
"""
from typing import List

def threeSum(nums: List[int]) -> List[List[int]]:
    nums.sort()  # 先排序，O(n log n)，使双指针和去重变得可能
    result: list[list[int]] = []
    n = len(nums)

    for i in range(n - 2):  # 至少需要 3 个元素
        # 剪枝优化：排序后 nums[i] 是最小的，如果它大于 0，三数之和不可能为 0
        if nums[i] > 0:
            break

        # 去重：跳过与前一个元素相同的值，避免生成重复三元组
        # 注意条件 i > 0，防止索引越界
        if i > 0 and nums[i] == nums[i - 1]:
            continue

        left, right = i + 1, n - 1  # 双指针：从 i+1 和末尾开始向中间移动

        while left < right:
            total = nums[i] + nums[left] + nums[right]

            if total == 0:
                result.append([nums[i], nums[left], nums[right]])

                # 找到答案后需要去重：跳过左右指针的重复元素
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1

                left += 1  # 继续搜索下一个可能的组合
                right -= 1
            elif total < 0:
                # 总和太小，需要增大：左指针右移（因为数组已排序）
                left += 1
            else:
                # 总和太大，需要减小：右指针左移
                right -= 1

    return result

if __name__ == "__main__":
    result = threeSum([-1, 0, 1, 2, -1, -4])
    expected = [[-1, -1, 2], [-1, 0, 1]]
    # 排序后比较
    assert sorted([sorted(x) for x in result]) == sorted([sorted(x) for x in expected])

    assert threeSum([0, 1, 1]) == []
    assert threeSum([0, 0, 0]) == [[0, 0, 0]]
    print("全部通过 ✓")
