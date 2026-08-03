"""
考点：Array, Dynamic Programming
题目：Best Time to Buy and Sell Stock（买卖股票的最佳时机）
题目描述：给定股票价格数组，只能买卖一次，求最大利润。不能获取利润返回 0。
示例 1：[7,1,5,3,6,4]，输出 5（1 买入，6 卖出）
示例 2：[7,6,4,3,1]，输出 0（没有交易）
思路：遍历维护最低价格，计算每天卖出可得的最大利润。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def maxProfit(prices: list[int]) -> int:
    # 使用 Python 的 float("inf") 表示正无穷大
    min_price: float = float("inf")
    max_profit: int = 0

    for price in prices:
        if price < min_price:
            # 找到更低的买入价
            min_price = price
        else:
            # 计算以当前价卖出的利润，并更新最大利润
            max_profit = max(max_profit, price - min_price)

    return max_profit


if __name__ == "__main__":
    assert maxProfit([7, 1, 5, 3, 6, 4]) == 5
    assert maxProfit([7, 6, 4, 3, 1]) == 0
    assert maxProfit([1, 2]) == 1
    assert maxProfit([1]) == 0
