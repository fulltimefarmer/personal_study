"""
考点：贪心, 数组, 动态规划
题目：Best Time to Buy and Sell Stock with Transaction Fee（买卖股票的最佳时机含手续费）
题目描述：给定 prices[i] 和手续费 fee，可无限次交易，但每次卖出需支付 fee。求最大利润。
思路：DP 状态机。两个状态：hold（持有股票时的最大收益），cash（不持有股票时的最大收益）。cash = max(cash, hold+prices[i]-fee)；hold = max(hold, cash-prices[i])。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def maxProfit(prices: list[int], fee: int) -> int:
    # hold: 当天结束时持有股票的最大收益（初始买入第一天的股票）
    hold = -prices[0]
    # cash: 当天结束时不持有股票的最大收益
    cash = 0

    for i in range(1, len(prices)):
        # 不持有 -> 卖出股票：cash = max(前天不持有, 昨天持有 + 今天卖出 - 手续费)
        cash = max(cash, hold + prices[i] - fee)
        # 持有 -> 买入股票：hold = max(昨天持有, 前天不持有 - 今天买入)
        hold = max(hold, cash - prices[i])

    # 最终不持有股票一定比持有股票收益高（不考虑手续费的话，也可以持有到最后）
    return cash


if __name__ == "__main__":
    # 示例：prices=[1,3,2,8,4,9], fee=2 → 输出: 8
    # 策略：买入 1，卖出 3（利润 0，不赚不亏）；买入 2，卖出 8（利润 4）；买入 4，卖出 9（利润 3）... 总计 8
    assert maxProfit([1, 3, 2, 8, 4, 9], 2) == 8
    # 示例：prices=[1,3,7,5,10,3], fee=3 → 输出: 6
    assert maxProfit([1, 3, 7, 5, 10, 3], 3) == 6
