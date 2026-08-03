"""
考点：Array, Dynamic Programming
题目：Maximum Product Subarray（乘积最大子数组）
题目描述：找出数组中乘积最大的连续子数组。
示例 1：[2,3,-2,4]，输出 6（子数组 [2,3]）
示例 2：[-2,0,-1]，输出 0
思路：DP，同时维护最大乘积和最小乘积（负负得正）。
cur_max = max(num, max_dp*num, min_dp*num)
cur_min = min(num, max_dp*num, min_dp*num)
时间复杂度：O(n)
空间复杂度：O(1)
"""


def maxProduct(nums: list[int]) -> int:
    # 初始化最大值、最小值、结果都为第一个元素
    max_dp: int = nums[0]  # 以当前位置结尾的最大乘积
    min_dp: int = nums[0]  # 以当前位置结尾的最小乘积（绝对值最大的负数）
    result: int = nums[0]

    for i in range(1, len(nums)):
        num: int = nums[i]
        # 必须暂存上一轮的 max_dp 和 min_dp，因为两个更新相互依赖
        prev_max: int = max_dp
        prev_min: int = min_dp
        # 新 max_dp 有三种可能：单独当前数、当前数×之前的最大值、当前数×之前的最小值（负负得正）
        max_dp = max(num, prev_max * num, prev_min * num)
        # 新 min_dp 同理：为可能的下一个"负负得正"做准备
        min_dp = min(num, prev_max * num, prev_min * num)
        # 更新全局最大值
        result = max(result, max_dp)

    return result


if __name__ == "__main__":
    assert maxProduct([2, 3, -2, 4]) == 6
    assert maxProduct([-2, 0, -1]) == 0
    assert maxProduct([-2]) == -2
    assert maxProduct([-4, -3]) == 12
