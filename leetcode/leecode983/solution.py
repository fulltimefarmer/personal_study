"""
考点：数组, 动态规划
题目：Minimum Cost For Tickets（最低票价）
题目描述：旅行日数组 days，三种票：1天/7天/30天，对应票价 costs[0]/costs[1]/costs[2]。求覆盖所有旅行日的最低花费。
思路：DP。dp[i] 表示到第 i 天的最小花费。非旅行日 dp[i]=dp[i-1]；旅行日 dp[i]=min(dp[i-1]+c0, dp[max(0,i-7)]+c1, dp[max(0,i-30)]+c2)。
时间复杂度：O(365)
空间复杂度：O(365)
"""


def mincostTickets(days: list[int], costs: list[int]) -> int:
    # 将旅行日转为集合，方便 O(1) 判断某天是否需要旅行
    day_set = set(days)
    last_day = days[-1]  # 最后一天旅行日

    # dp[i] 表示覆盖前 i 天所需的最低花费
    dp = [0] * (last_day + 1)

    for i in range(1, last_day + 1):
        if i not in day_set:
            # 非旅行日：不需要买票，花费和前一天相同
            dp[i] = dp[i - 1]
        else:
            # 旅行日：考虑三种购票方案，取最小值
            # 1 天票：昨天花费 + 1 天票价
            cost1 = dp[i - 1] + costs[0]
            # 7 天票：7 天前花费 + 7 天票价
            # max(0, i - 7) 防止索引越界到负数
            cost7 = dp[max(0, i - 7)] + costs[1]
            # 30 天票：30 天前花费 + 30 天票价
            cost30 = dp[max(0, i - 30)] + costs[2]
            dp[i] = min(cost1, cost7, cost30)

    return dp[last_day]


if __name__ == "__main__":
    # 示例：days=[1,4,6,7,8,20], costs=[2,7,15] → 输出: 11
    assert mincostTickets([1, 4, 6, 7, 8, 20], [2, 7, 15]) == 11
    # 示例：days=[1,2,3,4,5,6,7,8,9,10,30,31], costs=[2,7,15] → 输出: 17
    assert mincostTickets([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30, 31], [2, 7, 15]) == 17
