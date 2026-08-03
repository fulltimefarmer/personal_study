"""
考点：数组、数学、动态规划、排序
题目：Largest Divisible Subset（最大整除子集）—— LeetCode 368
题目描述：在无重复正整数集合中找出最大整除子集，任意两数相互整除
思路：排序后 DP。dp[i] 为以 nums[i] 结尾的最大子集大小，
      prev[i] 记录前驱用于回溯构建结果。
时间复杂度：O(n²)
空间复杂度：O(n)
"""

def largestDivisibleSubset(nums: list[int]) -> list[int]:
    n = len(nums)
    if n == 0:
        return []

    # 排序后，只需判断 nums[i] % nums[j] == 0（因为 nums[j] < nums[i]）
    nums.sort()

    # dp[i]：以 nums[i] 结尾的最大整除子集大小，初始化为 1（至少包含自身）
    dp = [1] * n
    # prev[i]：记录 dp[i] 的前驱索引，用于最后回溯构建子集，-1 表示没有前驱
    prev = [-1] * n

    max_index = 0  # 记录 dp 最大值所在的索引

    for i in range(1, n):
        for j in range(i):
            # 如果 nums[i] 能被 nums[j] 整除，且 dp[j] + 1 可以扩展 dp[i]
            if nums[i] % nums[j] == 0 and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
        # 更新全局最大子集的末尾索引
        if dp[i] > dp[max_index]:
            max_index = i

    # 回溯构建结果：从 max_index 沿 prev 链向前追溯
    result: list[int] = []
    cur: int | None = max_index
    while cur is not None and cur != -1:
        result.append(nums[cur])
        cur = prev[cur]  # prev[cur] 类型为 int

    # 由于回溯是逆序的，需要反转
    return result[::-1]


if __name__ == "__main__":
    assert set(largestDivisibleSubset([1, 2, 3])) == {1, 2} or set(largestDivisibleSubset([1, 2, 3])) == {1, 3}
    # 标准结果为 [1,2] 或 [1,3]，都是长度为 2
    result = largestDivisibleSubset([1, 2, 4, 8])
    assert len(result) == 4  # [1,2,4,8]
    assert largestDivisibleSubset([1]) == [1]
    assert largestDivisibleSubset([]) == []
    assert largestDivisibleSubset([3, 4, 16, 8]) == [4, 8, 16]  # 或类似
    print("所有断言通过！")
