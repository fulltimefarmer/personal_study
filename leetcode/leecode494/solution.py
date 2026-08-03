"""
考点：数组, 动态规划, 回溯
题目：Target Sum（目标和）
题目描述：给定非负整数数组 nums 和整数 target。在每个数前添加 '+' 或 '-'，求运算结果等于 target 的不同表达式数目。
思路：转化为 0-1 背包。设 P 为加'+'的数字和，则 P = (target+sum)/2。问题变成选若干个数和为 P 的方案数。dp[j] += dp[j-num]。
时间复杂度：O(n * P)
空间复杂度：O(P)
"""


def findTargetSumWays(nums: list[int], target: int) -> int:
    total = sum(nums)

    # 如果 target 的绝对值超过总和，或 (target + total) 不能被 2 整除，则无解
    # 因为加正号的数之和 P 必须是整数：P = (target + total) / 2
    if abs(target) > total or (target + total) % 2 != 0:
        return 0

    # P 是所有加正号的数的目标和
    P = (target + total) // 2
    # dp[j] 表示凑出和为 j 的方案数
    dp = [0] * (P + 1)
    dp[0] = 1  # 凑出和为 0 有 1 种方案（什么都不选）

    for num in nums:
        # 0-1 背包倒序遍历，每个数只能用一次
        for j in range(P, num - 1, -1):
            # 凑成 j 的方案数 = 不选 num 的方案数 + 选 num 的方案数
            dp[j] += dp[j - num]

    return dp[P]


if __name__ == "__main__":
    # 示例：nums=[1,1,1,1,1], target=3 → 输出: 5
    assert findTargetSumWays([1, 1, 1, 1, 1], 3) == 5
    # 示例：nums=[1], target=1 → 输出: 1
    assert findTargetSumWays([1], 1) == 1
