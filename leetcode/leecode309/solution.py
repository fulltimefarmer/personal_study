"""
考点：数组、动态规划
题目：Best Time to Buy and Sell Stock with Cooldown（最佳买卖股票时机含冷冻期）—— LeetCode 309
题目描述：多次买卖股票，卖出后有一天冷冻期，求最大利润
思路：DP 三状态。持有/当天卖出(冷冻)/不持有不冷冻。
      dp0 = max(dp0, dp2 - price)，dp1 = dp0 + price，dp2 = max(dp1, dp2)
时间复杂度：O(n)
空间复杂度：O(1)
"""

def maxProfit(prices: list[int]) -> int:
    # dp0：持有股票状态下的最大利润（初始化为负无穷，因为第一天还未买入）
    dp0 = float("-inf")
    # dp1：刚卖出股票（处于冷冻期）状态下的最大利润
    dp1 = 0
    # dp2：不持有股票且不在冷冻期状态下的最大利润
    dp2 = 0

    for price in prices:
        # 同时计算新状态，使用旧值避免相互影响
        # new_dp0：要么继续持有，要么在非冷冻期买入（dp2 - price）
        new_dp0 = max(dp0, dp2 - price)
        # new_dp1：卖出股票，由持有状态转换而来（dp0 + price）
        new_dp1 = dp0 + price
        # new_dp2：要么继续不持有，要么冷冻期解除（取冷冻期和非冷冻期中较大者）
        new_dp2 = max(dp1, dp2)

        dp0, dp1, dp2 = new_dp0, new_dp1, new_dp2

    # 最终状态：要么刚卖出（冷冻期），要么不持有且非冷冻期，取较大值
    return max(dp1, dp2)


if __name__ == "__main__":
    assert maxProfit([1, 2, 3, 0, 2]) == 3  # 买1卖2(1) + 买0卖2(2) = 3
    assert maxProfit([1]) == 0  # 只有一天，无法卖出，利润为 0
    assert maxProfit([1, 2, 4]) == 3  # 买1卖4
    assert maxProfit([2, 1, 4]) == 3  # 买1卖4
    assert maxProfit([6, 1, 3, 2, 4, 7]) == 6  # 买1卖3(2) + 买2卖7(5) = 7，wait, 有冷冻期：买1卖3, 冷冻, 买2卖7 = 2+5 = 7, 但实际更优的是买1卖7? 不行，中间有隔天。验证：买1卖3=2，冷冻1天无法买2，只能买4后一天？这题需要测试
    print("所有断言通过！")
