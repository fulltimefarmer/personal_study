"""
考点：数组、二分查找、动态规划
题目：Longest Increasing Subsequence（最长递增子序列）—— LeetCode 300
题目描述：给定整数数组，求最长严格递增子序列的长度
思路：贪心 + 二分。维护 tails 数组，tails[k] 为长度 k+1 的 LIS 的最小结尾。
      遍历 nums，二分查找插入位置，若比所有都大则追加，否则替换。
时间复杂度：O(n log n)
空间复杂度：O(n)
"""

import bisect


def lengthOfLIS(nums: list[int]) -> int:
    # tails[k] 表示长度为 k+1 的递增子序列的最小结尾元素
    # 贪心策略：结尾越小，后续扩展的可能性越大
    tails: list[int] = []

    for num in nums:
        # bisect.bisect_left(a, x)：在已排序列表 a 中二分查找 x 的插入位置
        # 返回第一个 >= x 的索引（左边界），保持递增序列
        pos = bisect.bisect_left(tails, num)

        if pos == len(tails):
            # num 比所有 tails 元素都大，可以扩展 LIS 长度
            tails.append(num)
        else:
            # 替换 tails[pos]，保持 tails[pos] 是最小可能的结尾元素
            tails[pos] = num

    return len(tails)


if __name__ == "__main__":
    assert lengthOfLIS([10, 9, 2, 5, 3, 7, 101, 18]) == 4  # [2, 3, 7, 101]
    assert lengthOfLIS([0, 1, 0, 3, 2, 3]) == 4  # [0, 1, 2, 3]
    assert lengthOfLIS([7, 7, 7, 7, 7, 7, 7]) == 1
    assert lengthOfLIS([1]) == 1
    assert lengthOfLIS([]) == 0
    print("所有断言通过！")
