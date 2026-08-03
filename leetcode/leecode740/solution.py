"""
考点：数组, 哈希表, 动态规划
题目：Delete and Earn（删除并获得点数）
题目描述：每次选择 nums[i] 获得 nums[i] 点数，但必须删除所有 nums[i]-1 和 nums[i]+1。求最大点数。
思路：转化为打家劫舍。统计每个值出现的总点数，points[val]=val*count。问题变为在 points 数组中不能取相邻元素的最大和（即打家劫舍问题）。用滚动变量优化。
时间复杂度：O(N + maxVal)
空间复杂度：O(maxVal)
"""


def deleteAndEarn(nums: list[int]) -> int:
    if not nums:
        return 0

    # 找到数组中的最大值，确定 points 数组长度
    max_val = max(nums)

    # points[i] 表示选择数字 i 能获得的总点数（i * 出现次数）
    points = [0] * (max_val + 1)
    for num in nums:
        points[num] += num  # 累加同一数字多次出现时的总点数

    # 转化为"打家劫舍"问题：不能取相邻元素的 points 数组的最大和
    # prev2 = dp[i-2], prev1 = dp[i-1]，滚动变量空间优化
    prev2 = 0  # 不取第一个数时的最大点数
    prev1 = points[0]  # 取第一个数时的最大点数

    for i in range(1, max_val + 1):
        # 当前最大 = max(不取当前数(prev1), 取当前数(prev2 + points[i]))
        curr = max(prev1, prev2 + points[i])
        # 滚动更新：prev2 前进到 prev1，prev1 前进到 curr
        prev2 = prev1
        prev1 = curr

    return prev1


if __name__ == "__main__":
    # 示例：[3,4,2] → 输出: 6（取 3 和 4？不行因为 3+1=4；取 2+4=6 是最优）
    assert deleteAndEarn([3, 4, 2]) == 6
    # 示例：[2,2,3,3,3,4] → 输出: 9（删除 3 获得 9 点，同时删除所有 2 和 4）
    assert deleteAndEarn([2, 2, 3, 3, 3, 4]) == 9
