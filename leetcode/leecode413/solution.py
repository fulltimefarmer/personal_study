"""
考点：数组、动态规划
题目：Arithmetic Slices（等差数列划分）—— LeetCode 413
题目描述：统计数组中所有等差子数组（连续、长度 >= 3）的个数
思路：DP。若 nums[i]-nums[i-1] == nums[i-1]-nums[i-2]，
      dp = dp + 1（所有以 i-1 结尾的等差子数组可接上 i，再加新的三元组）
      累加 dp 到总结果。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def numberOfArithmeticSlices(nums: list[int]) -> int:
    n = len(nums)
    if n < 3:
        return 0  # 少于 3 个元素，无法构成等差数列

    dp: int = 0    # 以当前位置结尾的等差子数组数量（长度 >= 3）
    total: int = 0  # 总等差子数组数量

    # 从索引 2 开始（第三个数），检查是否能构成等差数列
    for i in range(2, n):
        # 检查当前三个数是否构成等差数列
        if nums[i] - nums[i - 1] == nums[i - 1] - nums[i - 2]:
            # dp 的含义：如果前 i 个元素构成等差，则新增的等差子数组数 = 前一个 dp + 1
            # 例如 1,2,3,4：到 3 时 dp=1 ([1,2,3])，到 4 时 dp=2 ([2,3,4] 和 [1,2,3,4])
            dp += 1
            total += dp
        else:
            # 差不同，重置 dp
            dp = 0

    return total


if __name__ == "__main__":
    assert numberOfArithmeticSlices([1, 2, 3, 4]) == 3  # [1,2,3], [2,3,4], [1,2,3,4]
    assert numberOfArithmeticSlices([1]) == 0
    assert numberOfArithmeticSlices([1, 2, 3]) == 1    # [1,2,3]
    assert numberOfArithmeticSlices([1, 2, 3, 5, 7]) == 2  # [1,2,3] 和 [3,5,7]
    assert numberOfArithmeticSlices([7, 7, 7, 7]) == 3  # 等差=0: [0,1,2],[1,2,3],[0,1,2,3]
    print("所有断言通过！")
