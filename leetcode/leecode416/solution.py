"""
考点：数组、动态规划（0-1 背包）
题目：Partition Equal Subset Sum（分割等和子集）—— LeetCode 416
题目描述：判断能否将数组分成两个和相等的子集
思路：0-1 背包。总和的奇偶快速判断，target = sum/2。
      dp[i] = dp[i] || dp[i - num]，从 target 到 num 逆向遍历防止重复使用。
时间复杂度：O(n × sum)
空间复杂度：O(sum)
"""

def canPartition(nums: list[int]) -> bool:
    total = sum(nums)

    # 总和为奇数，不可能分成两个相等和
    if total % 2 != 0:
        return False

    target = total // 2  # 子集目标和

    # dp[i] 表示能否从 nums 中选出一些数，使其和为 i
    # 初始化大小为 target + 1，只有和为 0 是可达的
    dp = [False] * (target + 1)
    dp[0] = True  # 空子集和为 0

    for num in nums:
        # 逆向遍历（从 target 到 num）：保证每个数字只用一次（0-1 背包）
        # 如果正向遍历，num 可能被重复使用，变成完全背包
        for i in range(target, num - 1, -1):
            # dp[i] 可达的条件：之前 dp[i] 可达 或 dp[i - num] 可达
            dp[i] = dp[i] or dp[i - num]

    return dp[target]


if __name__ == "__main__":
    assert canPartition([1, 5, 11, 5]) is True   # [1, 5, 5] 和 [11]
    assert canPartition([1, 2, 3, 5]) is False   # 总和 11 为奇数?
    # 总和 11 为奇数
    assert canPartition([2, 2, 3, 5]) is False   # 总和 12, 子集和应为 6, 无法凑出
    assert canPartition([1, 1]) is True           # [1] 和 [1]
    assert canPartition([1, 2, 5]) is False       # 总和 8, 目标和 4, 无法凑出
    assert canPartition([3, 3, 3, 4, 5]) is True  # [3,3,3] 和 [4,5]
    print("所有断言通过！")
