"""
考点：数组, 动态规划
题目：Last Stone Weight II（最后一块石头的重量II）
题目描述：stones[i] 表示石头重量。每次取两块粉碎，x<=y 时 x 粉碎、y 变 y-x。求最后剩下石头的最小重量。
思路：转为 0-1 背包。将石头分成两堆，使重量差最小。问题等价于：选子集使其和尽量接近 sum/2。dp[j] 表示能选出和为 j 的子集。最后剩余最小重量 = sum - 2 * 最接近 sum/2 且可达的子集和。
时间复杂度：O(n * sum/2)
空间复杂度：O(sum/2)
"""


def lastStoneWeightII(stones: list[int]) -> int:
    total = sum(stones)
    target = total // 2  # 目标：选出总和最接近 total/2 的子集

    # dp[j] 表示能否选出和为 j 的石头子集
    dp = [False] * (target + 1)
    dp[0] = True  # 空集和为 0

    for stone in stones:
        # 0-1 背包倒序遍历，每块石头只能用一次
        for j in range(target, stone - 1, -1):
            # dp[j] 为 True 的条件：之前就能凑出 j，或者之前能凑出 j-stone
            # 布尔运算符 or 短路求值
            dp[j] = dp[j] or dp[j - stone]

    # 从 target 向下找第一个能凑出的和，即为最接近 target 的子集和
    for j in range(target, -1, -1):
        if dp[j]:
            # 最后剩余的最小重量 = 两堆重量之差 = total - 2 * j
            return total - 2 * j

    return 0


if __name__ == "__main__":
    # 示例：[2,7,4,1,8,1] → 输出: 1
    assert lastStoneWeightII([2, 7, 4, 1, 8, 1]) == 1
    # 示例：[31,26,33,21,40] → 输出: 5
    assert lastStoneWeightII([31, 26, 33, 21, 40]) == 5
