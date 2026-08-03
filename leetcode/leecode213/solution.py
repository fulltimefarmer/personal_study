"""
考点：数组、动态规划
题目：House Robber II（打家劫舍 II）
思路：房屋围成一圈，分两种情况——不偷第一间（nums[1:]）和不偷最后一间（nums[:-1]），
      分别用 House Robber I 的 DP，取最大值。n=1 直接返回 nums[0]。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def robII(nums: list[int]) -> int:
    n = len(nums)
    if n == 1:
        return nums[0]  # 只有一间房，直接偷

    def rob_range(start: int, end: int) -> int:
        """在 nums[start:end+1] 范围内运行打家劫舍 I 的 DP"""
        prev2 = 0  # dp[i-2]
        prev1 = 0  # dp[i-1]
        for i in range(start, end + 1):
            cur = max(prev1, prev2 + nums[i])
            prev2 = prev1
            prev1 = cur
        return prev1

    # 情况 1：不偷最后一间 → 范围 [0, n-2]
    # 情况 2：不偷第一间 → 范围 [1, n-1]
    return max(rob_range(0, n - 2), rob_range(1, n - 1))


if __name__ == "__main__":
    # 示例 1: [2,3,2] → 3 (偷第二间)
    assert robII([2, 3, 2]) == 3
    # 示例 2: [1,2,3,1] → 4 (偷 1+3)
    assert robII([1, 2, 3, 1]) == 4
    # 示例 3: [1] → 1
    assert robII([1]) == 1
    print("全部测试通过")
