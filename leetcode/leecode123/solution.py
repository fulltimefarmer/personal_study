"""
考点：Array, Dynamic Programming
题目：Best Time to Buy and Sell Stock III（买卖股票的最佳时机III）
题目描述：最多完成两笔交易，求最大利润（不能同时持有多股）。
示例 1：[3,3,5,0,0,3,1,4]，输出 6（0→3 + 1→4）
示例 2：[1,2,3,4,5]，输出 4
示例 3：[7,6,4,3,1]，输出 0
思路：状态机 DP，buy1/sell1/buy2/sell2 四个状态紧凑递推。
buy1: 第一次买入后的最大现金 = max(之前buy1, -price)
sell1: 第一次卖出后的最大现金 = max(之前sell1, buy1+price)
buy2: 第二次买入后的最大现金 = max(之前buy2, sell1-price)
sell2: 第二次卖出后的最大现金 = max(之前sell2, buy2+price)
时间复杂度：O(n)
空间复杂度：O(1)
"""


def maxProfit3(prices: list[int]) -> int:
    # float("-inf") 表示负无穷大，初始化为"不可能更差"的值
    buy1: float = float("-inf")
    sell1: int = 0
    buy2: float = float("-inf")
    sell2: int = 0

    for price in prices:
        # 四个状态按顺序更新，每个状态依赖上一个状态在当前天的值
        buy1 = max(buy1, -price)              # 第一次买入：取最便宜的买入价
        sell1 = max(sell1, buy1 + price)      # 第一次卖出：在buy1基础上卖出
        buy2 = max(buy2, sell1 - price)       # 第二次买入：在sell1基础上买入
        sell2 = max(sell2, buy2 + price)      # 第二次卖出：在buy2基础上卖出

    return sell2


if __name__ == "__main__":
    assert maxProfit3([3, 3, 5, 0, 0, 3, 1, 4]) == 6
    assert maxProfit3([1, 2, 3, 4, 5]) == 4
    assert maxProfit3([7, 6, 4, 3, 1]) == 0
    assert maxProfit3([1]) == 0
