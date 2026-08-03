"""
考点：数组、动态规划（区间DP）
题目：Burst Balloons（戳气球）—— LeetCode 312
题目描述：戳气球得分等于相邻三个气球数字乘积，求最大分数
思路：区间 DP。反过来想，考虑开区间 (i,j) 中最后一个戳的气球 k。
      dp[i][j] = max(dp[i][k] + dp[k][j] + nums[i]*nums[k]*nums[j])
时间复杂度：O(n³)
空间复杂度：O(n²)
"""

def maxCoins(nums: list[int]) -> int:
    n = len(nums)
    # 在数组首尾各加 1，方便处理边界（首尾的气球乘以 1）
    arr = [1] + nums + [1]

    # dp[i][j] 表示戳破开区间 (i, j) 内所有气球能获得的最大金币数
    # 区间长度为 len，从 2 开始（因为开区间至少包含 i+1）
    dp: list[list[int]] = [[0] * (n + 2) for _ in range(n + 2)]

    # 按区间长度从小到大遍历，保证计算大区间时小区间已计算完毕
    for length in range(2, n + 2):  # length 从 2 到 n+1
        for i in range(0, n + 2 - length):
            j = i + length
            # 枚举区间内最后一个被戳破的气球 k
            for k in range(i + 1, j):
                # 当 k 是 (i, j) 中最后一个被戳破的气球时：
                # 左半边 (i, k) 和右半边 (k, j) 已经戳完
                # 此时 k 的邻居是 arr[i] 和 arr[j]
                coins = dp[i][k] + dp[k][j] + arr[i] * arr[k] * arr[j]
                dp[i][j] = max(dp[i][j], coins)

    return dp[0][n + 1]  # 整个开区间 (0, n+1) 的最大值


if __name__ == "__main__":
    assert maxCoins([3, 1, 5, 8]) == 167  # 戳 1 → 3*1*5=15, 戳 5 → 3*5*8=120, 戳 3 → 1*3*8=24, 戳 8 → 1*8*1=8, 总=167
    assert maxCoins([1, 5]) == 10  # arr=[1,1,5,1]: dp[0][3] = max(dp[0][1]+dp[1][3]+1*1*5=5, dp[0][2]+dp[2][3]+1*5*1=5+5=10)
    assert maxCoins([1]) == 1
    assert maxCoins([]) == 0
    print("所有断言通过！")
