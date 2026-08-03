"""
考点：BFS、数组、动态规划
题目：Coin Change（零钱兑换）—— LeetCode 322
题目描述：给定硬币面额和总金额，求所需最少硬币数，无解返回 -1
思路：动态规划（完全背包）。dp[i] = min(dp[i - coin] + 1)
时间复杂度：O(amount × n)
空间复杂度：O(amount)
"""

def coinChange(coins: list[int], amount: int) -> int:
    # dp[i] 表示凑出金额 i 所需的最少硬币数
    # 初始化为 float("inf") 表示暂时不可达
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0  # 金额 0 需要 0 个硬币

    # 完全背包：因为每种硬币可以无限使用，所以从小到大遍历容量 i
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                # 状态转移：使用一枚面值 coin 的硬币，剩余金额 i-coin 的最优解 + 1
                dp[i] = min(dp[i], dp[i - coin] + 1)

    # 如果 dp[amount] 仍为 inf，说明无法凑出该金额
    return int(dp[amount]) if dp[amount] != float("inf") else -1


if __name__ == "__main__":
    assert coinChange([1, 2, 5], 11) == 3  # 5 + 5 + 1
    assert coinChange([2], 3) == -1  # 无法凑出
    assert coinChange([1], 0) == 0  # 金额 0
    assert coinChange([1], 1) == 1
    assert coinChange([1], 2) == 2
    assert coinChange([186, 419, 83, 408], 6249) == 20
    print("所有断言通过！")
