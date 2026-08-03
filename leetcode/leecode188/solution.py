"""
考点：数组、动态规划
题目：Best Time to Buy and Sell Stock IV（买卖股票的最佳时机 IV）
思路：DP，dp[i][j] 表示前 j 天最多 i 次交易的最大利润。
      maxPrev 维护 dp[i-1][j-1]-prices[j-1] 的最大值。
      若 k >= n/2，相当于无限交易，累加所有正利润。
时间复杂度：O(k × n)
空间复杂度：O(n)
"""


def maxProfitIV(k: int, prices: list[int]) -> int:
    n = len(prices)
    if n == 0:
        return 0

    # 如果 k 足够大，等同于可以无限交易
    # 此时只要价格涨了就交易（贪心），累加所有正利润
    if k >= n // 2:
        return sum(max(prices[i] - prices[i - 1], 0) for i in range(1, n))

    # dp[j] 表示前 j 天最多当前 i 次交易的最大利润
    dp = [0] * n

    # 外层循环：交易次数 i
    for _ in range(1, k + 1):
        # maxPrev 维护 dp_prev[j-1] - prices[j-1] 的最大值
        maxPrev = -prices[0]
        prevProfit = 0  # 保存上一轮 dp[j] 的值
        for j in range(1, n):
            temp = dp[j]  # 暂存当前值，作为下一轮的 prevProfit
            # 要么不交易(dp[j-1])，要么在 maxPrev 最佳时刻买入、j 时刻卖出
            dp[j] = max(dp[j - 1], prices[j] + maxPrev)
            # 更新 maxPrev：考虑在第 j 天买入的情况
            maxPrev = max(maxPrev, prevProfit - prices[j])
            prevProfit = temp

    return dp[n - 1]


if __name__ == "__main__":
    # 示例: k=2, prices=[3,2,6,5,0,3] → 7
    assert maxProfitIV(2, [3, 2, 6, 5, 0, 3]) == 7
    # 示例: k=2, prices=[] → 0
    assert maxProfitIV(2, []) == 0
    print("全部测试通过")
