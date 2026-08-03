"""
考点：数组
题目：Summary Ranges（汇总区间）
思路：遍历，当 nums[i]!=nums[i-1]+1 时结束上一个区间；循环结束后处理最后一个区间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def summaryRanges(nums: list[int]) -> list[str]:
    result: list[str] = []
    n = len(nums)
    if n == 0:
        return result

    start = nums[0]  # 当前区间的起始值

    for i in range(1, n):
        # 如果不连续（当前值 != 前一个值+1），结束上一个区间
        if nums[i] != nums[i - 1] + 1:
            if start == nums[i - 1]:
                # 区间只有一个数
                result.append(str(start))
            else:
                # 区间有多个数，格式为 "start→end"
                result.append(f"{start}->{nums[i - 1]}")
            start = nums[i]  # 开始新区间

    # 处理最后一个区间
    if start == nums[n - 1]:
        result.append(str(start))
    else:
        result.append(f"{start}->{nums[n - 1]}")

    return result


if __name__ == "__main__":
    # 示例 1: [0,1,2,4,5,7] → ["0->2","4->5","7"]
    assert summaryRanges([0, 1, 2, 4, 5, 7]) == ["0->2", "4->5", "7"]
    # 示例 2: [0,2,3,4,6,8,9] → ["0","2->4","6","8->9"]
    assert summaryRanges([0, 2, 3, 4, 6, 8, 9]) == ["0", "2->4", "6", "8->9"]
    print("全部测试通过")
