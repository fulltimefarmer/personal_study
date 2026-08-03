"""
考点：数组、动态规划
题目：House Robber（打家劫舍）
题目描述：给定非负整数数组 nums 表示每家金额，不能偷相邻两家，求最大总金额。
  示例：nums = [2,7,9,3,1] → 12（偷 2+9+1）
思路：动态规划。dp[i] 表示前 i 家能偷的最大金额。
  状态转移：dp[i] = max(dp[i-1], dp[i-2] + nums[i])
  空间优化：只需两个变量 prev2（i-2）和 prev1（i-1）。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def rob(nums: list[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]

    # prev2 = dp[i-2], prev1 = dp[i-1]
    prev2 = nums[0]  # 只有一家时，偷这一家
    prev1 = max(nums[0], nums[1])  # 有两家时，偷金额大的那家

    for i in range(2, len(nums)):
        # 状态转移：要么不偷第 i 家（保持 prev1），要么偷第 i 家（prev2 + nums[i]）
        curr = max(prev1, prev2 + nums[i])
        prev2 = prev1  # 滚动更新
        prev1 = curr

    return prev1


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4
    assert rob([2, 7, 9, 3, 1]) == 12
    assert rob([2, 1, 1, 2]) == 4
