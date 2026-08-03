"""
考点：数组、动态规划
题目：Best Time to Buy and Sell Stock IV（买卖股票的最佳时机 IV）
题目描述：给定数组 prices 表示每天股价，最多完成 k 笔交易（买+卖算一笔），
  求最大利润。不能同时参与多笔交易。
  示例：k = 2, prices = [3,2,6,5,0,3] → 7
思路：动态规划。dp[i][j] 表示前 i 天最多进行 j 笔交易的最大收益。
  hold[i][j] 表示前 i 天进行了 j 笔交易且当天持有股票的最大收益。
  如果 k >= n/2，问题退化为无限次交易（贪心）。
时间复杂度：O(n*k)
空间复杂度：O(k)
"""


def maxProfit(k: int, prices: list[int]) -> int:
    n = len(prices)
    if n == 0:
        return 0

    # 如果 k 大于等于天数的一半，等价于可以无限次交易
    # 此时贪心：只要今天价格比昨天高就卖出
    if k >= n // 2:
        profit = 0
        for i in range(1, n):
            if prices[i] > prices[i - 1]:
                profit += prices[i] - prices[i - 1]
        return profit

    # buy[j]：进行了 j 笔交易后持有股票的最大收益
    # sell[j]：进行了 j 笔交易后不持有股票的最大收益
    buy = [-float("inf")] * (k + 1)
    sell = [0] * (k + 1)

    for price in prices:
        for j in range(1, k + 1):
            # 要么之前已经买了，要么今天买入（买入对应之前 sell[j-1] 的状态）
            buy[j] = max(buy[j], sell[j - 1] - price)
            # 要么之前已经卖了，要么今天卖出（卖出对应之前 buy[j] 的状态）
            sell[j] = max(sell[j], buy[j] + price)

    return sell[k]


if __name__ == "__main__":
    assert maxProfit(2, [2, 4, 1]) == 2
    assert maxProfit(2, [3, 2, 6, 5, 0, 3]) == 7
    assert maxProfit(2, []) == 0
