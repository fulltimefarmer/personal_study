"""
考点：数组、动态规划（排列背包）
题目：Combination Sum IV（组合总和IV）—— LeetCode 377
题目描述：给定不同整数数组和目标值，求排列数（顺序不同视为不同组合）
思路：DP 排列背包。外层遍历 target，内层遍历 nums。
      dp[i] += dp[i - num]（i 从 num 到 target）
      注意区别：组合背包外层是物品，排列背包外层是容量。
时间复杂度：O(target × n)
空间复杂度：O(target)
"""

def combinationSum4(nums: list[int], target: int) -> int:
    # dp[i] 表示总和为 i 的排列组合数
    dp = [0] * (target + 1)
    dp[0] = 1  # 和为 0 有一种方式（什么都不选）

    # 外层遍历容量（target 从小到大）：确保考虑顺序（排列）
    # 如果外层是物品（组合背包），则 {1,2} 和 {2,1} 算同一种
    for i in range(1, target + 1):
        for num in nums:
            if num <= i:
                # 排列背包转移方程：dp[i] += dp[i - num]
                dp[i] += dp[i - num]

    return dp[target]


if __name__ == "__main__":
    assert combinationSum4([1, 2, 3], 4) == 7
    # 组合: (1,1,1,1), (1,1,2), (1,2,1), (2,1,1), (2,2), (1,3), (3,1)
    assert combinationSum4([9], 3) == 0
    assert combinationSum4([1], 1) == 1
    assert combinationSum4([1, 2], 3) == 3  # (1,1,1), (1,2), (2,1)
    assert combinationSum4([3, 4, 5, 6, 7, 8, 9, 10], 10) == 9
    print("所有断言通过！")
