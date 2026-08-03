"""
考点：数组, 动态规划
题目：Uncrossed Lines（不相交的线）
题目描述：在 nums1 和 nums2 中连接相等的数字，连线不能相交。求最大连线数。
思路：本质是求 LCS（最长公共子序列）。dp[i][j] 表示 nums1[0..i-1] 和 nums2[0..j-1] 的 LCS 长度。nums1[i-1]==nums2[j-1] 则 dp[i][j]=dp[i-1][j-1]+1，否则 max(dp[i-1][j], dp[i][j-1])。
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""


def maxUncrossedLines(nums1: list[int], nums2: list[int]) -> int:
    m, n = len(nums1), len(nums2)
    # dp[i][j] 表示 nums1 前 i 个元素与 nums2 前 j 个元素的最大连线数（即 LCS 长度）
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if nums1[i - 1] == nums2[j - 1]:
                # 元素相等：可以连一条线 + 前一对元素的最大连线数
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 元素不等：取忽略 nums1 最后元素或忽略 nums2 最后元素的较大值
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


if __name__ == "__main__":
    # 示例：nums1=[1,4,2], nums2=[1,2,4] → 输出: 2
    assert maxUncrossedLines([1, 4, 2], [1, 2, 4]) == 2
    # 示例：nums1=[2,5,1,2,5], nums2=[10,5,2,1,5,2] → 输出: 3
    assert maxUncrossedLines([2, 5, 1, 2, 5], [10, 5, 2, 1, 5, 2]) == 3
    # 示例：nums1=[1,3,7,1,7,5], nums2=[1,9,2,5,1] → 输出: 2
    assert maxUncrossedLines([1, 3, 7, 1, 7, 5], [1, 9, 2, 5, 1]) == 2
