"""
考点：数组, 动态规划
题目：Min Cost Climbing Stairs（使用最小花费爬楼梯）
题目描述：cost[i] 是从第 i 阶向上爬的花费，每次可爬 1 或 2 阶。可从第 0 或第 1 阶开始。求到达顶部的最小花费。
思路：DP。到达第 i 阶的最小花费 = cost[i] + min(到达第 i-1 阶最小花费, 到达第 i-2 阶最小花费)。最终答案为 min(到达最后一阶, 到达倒数第二阶)。用两个变量滚动优化。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def minCostClimbingStairs(cost: list[int]) -> int:
    n = len(cost)
    # prev2: 到达第 i-2 阶的最小花费（初始为第 0 阶的花费）
    prev2 = cost[0]
    # prev1: 到达第 i-1 阶的最小花费（初始为第 1 阶的花费）
    prev1 = cost[1]

    # 从第 2 阶开始计算到达每一阶的最小花费
    for i in range(2, n):
        # 到达第 i 阶的最小花费 = 当前阶花费 + min(前一阶的最小花费, 前两阶的最小花费)
        curr = cost[i] + min(prev1, prev2)
        # 滚动更新变量
        prev2 = prev1
        prev1 = curr

    # 到达顶部可以从最后一阶或倒数第二阶直接跨过去，取较小值
    return min(prev1, prev2)


if __name__ == "__main__":
    # 示例：[10,15,20] → 输出: 15（从第 1 阶开始，爬两阶到顶部，花费 15）
    assert minCostClimbingStairs([10, 15, 20]) == 15
    # 示例：[1,100,1,1,1,100,1,1,100,1] → 输出: 6
    assert minCostClimbingStairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]) == 6
