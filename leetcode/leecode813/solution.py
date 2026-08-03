"""
考点：数组, 数学, 动态规划, 前缀和
题目：Largest Sum of Averages（最大平均值和的分组）
题目描述：将数组 nums 分成最多 k 个非空连续子数组，求各子数组平均值之和的最大值。
思路：DP+前缀和。dp[i][m] 表示前 i 个元素分 m 组的最大分数。dp[i][m] = max(dp[j][m-1] + (prefixSum[i]-prefixSum[j])/(i-j))。
时间复杂度：O(n² * k)
空间复杂度：O(n * k)
"""


def largestSumOfAverages(nums: list[int], k: int) -> float:
    n = len(nums)
    # 前缀和：prefix[i] = sum(nums[0:i])，即前 i 个元素的和（不包含 i）
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    # dp[i][m] 表示前 i 个元素分成 m 组时，各子数组平均值之和的最大值
    dp = [[0.0] * (k + 1) for _ in range(n + 1)]

    # 初始化：分成 1 组时，就是整个前缀的平均值
    for i in range(1, n + 1):
        dp[i][1] = prefix[i] / i

    # m: 分组数，从 2 到 k
    for m in range(2, k + 1):
        # i: 前 i 个元素，至少要 m 个元素才能分成 m 组
        for i in range(m, n + 1):
            # j: 分割点，前 j 个元素分 m-1 组，j+1 到 i 为第 m 组
            for j in range(m - 1, i):
                # 第 m 组的平均值 = (prefix[i] - prefix[j]) / (i - j)
                avg = (prefix[i] - prefix[j]) / (i - j)
                dp[i][m] = max(dp[i][m], dp[j][m - 1] + avg)

    return dp[n][k]


if __name__ == "__main__":
    # 示例：nums=[9,1,2,3,9], k=3 → 输出: 20.0
    result = largestSumOfAverages([9, 1, 2, 3, 9], 3)
    assert abs(result - 20.0) < 1e-6
    # 示例：nums=[1,2,3,4,5,6,7], k=4 → 输出: 20.5
    result = largestSumOfAverages([1, 2, 3, 4, 5, 6, 7], 4)
    assert abs(result - 20.5) < 1e-6
