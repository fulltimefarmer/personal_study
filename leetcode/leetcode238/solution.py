"""
考点：数组、前缀积
题目：Product of Array Except Self（除自身以外数组的乘积）
题目描述：返回数组 answer，其中 answer[i] 等于 nums 中除 nums[i] 之外其余各元素的乘积。
  要求 O(n) 时间，O(1) 额外空间（输出数组不计入）。
  示例：nums = [1,2,3,4] → [24,12,8,6]
思路：两次遍历。先从左到右计算前缀积（nums[i] 左侧所有元素的乘积），
  再从右到左乘上后缀积（nums[i] 右侧所有元素的乘积）。
时间复杂度：O(n)
空间复杂度：O(1)（不计输出数组）
"""


def productExceptSelf(nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [1] * n  # 初始化为 1，用于存储左侧前缀积和最终结果

    # 第一遍：从左到右计算前缀积
    # answer[i] 存储 nums[0] * nums[1] * ... * nums[i-1]
    prefix = 1
    for i in range(n):
        answer[i] = prefix  # 当前 answer[i] = 左侧所有元素的乘积
        prefix *= nums[i]  # prefix 更新为包含当前元素

    # 第二遍：从右到左乘上后缀积
    # answer[i] 再乘上 nums[i+1] * ... * nums[n-1]
    suffix = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= suffix  # answer[i] = 左侧积 * 右侧积
        suffix *= nums[i]  # suffix 更新为包含当前元素

    return answer


if __name__ == "__main__":
    assert productExceptSelf([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert productExceptSelf([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
