"""
考点：数组、动态规划
题目：House Robber（打家劫舍）
思路：dp[i]=max(dp[i-1], dp[i-2]+nums[i])，滚动变量优化为 O(1) 空间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def rob(nums: list[int]) -> int:
    # prev2: dp[i-2], prev1: dp[i-1]
    prev2 = 0  # 偷到前前家的最大金额
    prev1 = 0  # 偷到前家的最大金额

    for num in nums:
        # 当前的最大金额：要么不偷当前（保持 prev1），要么偷当前（prev2 + num）
        cur = max(prev1, prev2 + num)
        # 滚动更新：prev2 前移为 prev1，prev1 前移为 cur
        prev2 = prev1
        prev1 = cur

    return prev1


if __name__ == "__main__":
    # 示例 1: [1,2,3,1] → 4 (偷 1+3)
    assert rob([1, 2, 3, 1]) == 4
    # 示例 2: [2,7,9,3,1] → 12 (偷 2+9+1)
    assert rob([2, 7, 9, 3, 1]) == 12
    print("全部测试通过")
