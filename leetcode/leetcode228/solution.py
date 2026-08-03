"""
考点：数组
题目：Summary Ranges（汇总区间）
题目描述：给定无重复有序整数数组，返回其最小区间覆盖列表。
  示例：nums = [0,1,2,4,5,7] → ["0->2","4->5","7"]
思路：遍历数组，记录区间起点 start。当 nums[i] != nums[i-1] + 1 时，说明区间断开，
  将 [start, nums[i-1]] 加入结果，并更新 start = nums[i]。最后处理最后一个区间。
时间复杂度：O(n)
空间复杂度：O(1)（不计结果）
"""


def summaryRanges(nums: list[int]) -> list[str]:
    result: list[str] = []
    if not nums:
        return result

    start = nums[0]  # 当前区间的起点

    for i in range(1, len(nums)):
        # 当前数字不连续（nums[i] != nums[i-1] + 1），说明区间断开
        if nums[i] != nums[i - 1] + 1:
            # 区间只有一个数：直接加入该数
            if start == nums[i - 1]:
                result.append(str(start))
            else:
                # 区间有多个数：格式 "start->end"
                result.append(f"{start}->{nums[i - 1]}")
            start = nums[i]  # 开始新区间

    # 处理最后一个区间
    if start == nums[-1]:
        result.append(str(start))
    else:
        result.append(f"{start}->{nums[-1]}")

    return result


if __name__ == "__main__":
    assert summaryRanges([0, 1, 2, 4, 5, 7]) == ["0->2", "4->5", "7"]
    assert summaryRanges([0, 2, 3, 4, 6, 8, 9]) == ["0", "2->4", "6", "8->9"]
    assert summaryRanges([]) == []
    assert summaryRanges([-1]) == ["-1"]
