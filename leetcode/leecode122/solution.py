"""
考点：Greedy, Array, Dynamic Programming
题目：Best Time to Buy and Sell Stock II（买卖股票的最佳时机II）
题目描述：允许多次交易（同一天可买卖），求最大总利润。
示例 1：[7,1,5,3,6,4]，输出 7（1→5 得 4 + 3→6 得 3）
示例 2：[1,2,3,4,5]，输出 4
示例 3：[7,6,4,3,1]，输出 0
思路：贪心，累加所有 prices[i] > prices[i-1] 的差值。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def maxProfit2(prices: list[int]) -> int:
    profit: int = 0

    for i in range(1, len(prices)):
        # 只要今天的价格比昨天高，就把差累积加到利润中
        if prices[i] > prices[i - 1]:
            profit += prices[i] - prices[i - 1]

    return profit


if __name__ == "__main__":
    assert maxProfit2([7, 1, 5, 3, 6, 4]) == 7
    assert maxProfit2([1, 2, 3, 4, 5]) == 4
    assert maxProfit2([7, 6, 4, 3, 1]) == 0
    assert maxProfit2([1]) == 0
