"""
考点：数组, 二分搜索, 动态规划, 滑动窗口, 滚动哈希
题目：Maximum Length of Repeated Subarray（最长重复子数组）
题目描述：给定两个整数数组 nums1 和 nums2，返回它们的最长公共子数组的长度（子数组要连续）。
思路：DP。dp[i][j] 表示以 nums1[i-1] 和 nums2[j-1] 结尾的最长公共子数组长度。相等则 dp[i][j]=dp[i-1][j-1]+1，否则为 0。取最大值。
时间复杂度：O(m * n)
空间复杂度：O(m * n)
"""


def findLength(nums1: list[int], nums2: list[int]) -> int:
    m, n = len(nums1), len(nums2)
    # dp[i][j] 表示以 nums1[i-1] 和 nums2[j-1] 结尾的最长公共子数组的长度
    # 多一行一列方便处理边界条件，第 0 行/列初始为 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_len = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if nums1[i - 1] == nums2[j - 1]:
                # 相等时：在前一个状态基础上 +1
                dp[i][j] = dp[i - 1][j - 1] + 1
                # 更新全局最大长度
                max_len = max(max_len, dp[i][j])
            # 不相等时 dp[i][j] 自然为 0（初始值），不需要额外处理

    return max_len


if __name__ == "__main__":
    # 示例：nums1=[1,2,3,2,1], nums2=[3,2,1,4,7] → 输出: 3（公共子数组 [3,2,1]）
    assert findLength([1, 2, 3, 2, 1], [3, 2, 1, 4, 7]) == 3
    # 示例：nums1=[0,0,0,0,0], nums2=[0,0,0,0,0] → 输出: 5
    assert findLength([0, 0, 0, 0, 0], [0, 0, 0, 0, 0]) == 5
