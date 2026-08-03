"""
考点: Array, Divide and Conquer, Dynamic Programming
题目: Maximum Subarray（最大子数组和）
题目描述: 给定整数数组 nums，求具有最大和的连续子数组，返回最大和。
示例: nums = [-2,1,-3,4,-1,2,1,-5,4] -> 6（子数组 [4,-1,2,1]）
思路: Kadane 算法。dp[i] = max(nums[i], dp[i-1] + nums[i])，空间优化为 O(1)。
      遍历时维护 currentSum（以当前元素结尾的最大和）和 maxSum（全局最大和）。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def maxSubArray(nums: list[int]) -> int:
    # 初始化: 第一个元素结束时，最大和就是它本身
    current_sum = nums[0]
    max_sum = nums[0]

    # 从第二个元素开始遍历
    for i in range(1, len(nums)):
        # 核心决策: 要么另起炉灶(只取当前元素)，要么延续前面的子数组
        # max() 是 Python 内置函数，取两个数中的较大值
        current_sum = max(nums[i], current_sum + nums[i])
        # 更新全局最大和
        max_sum = max(max_sum, current_sum)

    return max_sum


if __name__ == "__main__":
    assert maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert maxSubArray([1]) == 1
    assert maxSubArray([5, 4, -1, 7, 8]) == 23
