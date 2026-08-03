"""
考点：数组, 动态规划
题目：Coin Change II（零钱兑换II）
题目描述：给定硬币面额 coins 和总金额 amount，求凑成总金额的硬币组合数。每种硬币无限使用。
思路：完全背包求组合数。dp[j] 表示金额 j 的组合数。外层硬币、内层金额正序：dp[j] += dp[j-coin]。注意：外层遍历硬币保证不重复计算组合顺序。
时间复杂度：O(n * amount)
空间复杂度：O(amount)
"""


def change(amount: int, coins: list[int]) -> int:
    # dp[j] 表示凑成金额 j 的组合数（不区分顺序）
    dp = [0] * (amount + 1)
    dp[0] = 1  # 凑成 0 元只有一种方式：什么都不选

    # 外层遍历硬币，确保硬币顺序固定，避免组合重复（如 1+2 和 2+1 被视为同一种）
    for coin in coins:
        # 完全背包正序遍历，每种硬币可无限使用
        for j in range(coin, amount + 1):
            # 凑成 j 元 = 不使用当前硬币 + 使用当前硬币（j-coin 的状态已考虑当前硬币）
            dp[j] += dp[j - coin]

    return dp[amount]


if __name__ == "__main__":
    # 示例：amount=5, coins=[1,2,5] → 输出: 4（5; 2+2+1; 2+1+1+1; 1+1+1+1+1）
    assert change(5, [1, 2, 5]) == 4
    # 示例：amount=3, coins=[2] → 输出: 0
    assert change(3, [2]) == 0
    # 示例：amount=10, coins=[10] → 输出: 1
    assert change(10, [10]) == 1
