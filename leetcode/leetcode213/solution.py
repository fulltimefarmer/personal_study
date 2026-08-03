"""
考点：数组、动态规划
题目：House Robber II（打家劫舍 II）
题目描述：同 LeetCode 198 打家劫舍，但房屋围成一圈，首尾相邻不能同时偷。
  示例：nums = [2,3,2] → 3（偷第二家）
思路：环形问题分解为两个线性问题。由于首尾不能同时偷，分别计算：
  1. 不偷第一家的情况：rob(nums[1:])
  2. 不偷最后一家的情况：rob(nums[:-1])
  取两者的最大值。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def rob(nums: list[int]) -> int:
    n = len(nums)
    if n == 1:
        return nums[0]  # 只有一家，直接偷

    def rob_range(start: int, end: int) -> int:
        """在 [start, end) 区间内做线性打家劫舍"""
        if start >= end:
            return 0
        prev2 = 0  # dp[i-2]
        prev1 = 0  # dp[i-1]
        for i in range(start, end):
            # 状态转移：max(不偷当前, 偷当前+dp[i-2])
            curr = max(prev1, prev2 + nums[i])
            prev2 = prev1  # 滚动
            prev1 = curr
        return prev1

    # 情况1：不偷第一家（从索引 1 开始）
    profit1 = rob_range(1, n)
    # 情况2：不偷最后一家（到索引 n-2 为止，即索引 0 到 n-1）
    profit2 = rob_range(0, n - 1)

    return max(profit1, profit2)


if __name__ == "__main__":
    assert rob([2, 3, 2]) == 3
    assert rob([1, 2, 3, 1]) == 4
    assert rob([1, 2, 3]) == 3
    assert rob([1]) == 1
