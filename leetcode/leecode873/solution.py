"""
考点：数组, 哈希表, 动态规划
题目：Length of Longest Fibonacci Subsequence（最长的斐波那契子序列的长度）
题目描述：给定严格递增数组 arr，找出最长的斐波那契式子序列（X_i + X_{i+1} = X_{i+2}）的长度，不存在返回 0。
思路：DP+哈希表。dp[i][j] 表示以 arr[i],arr[j] 结尾的斐波那契子序列长度。target=arr[j]-arr[i]，若存在且索引 k<i，则 dp[i][j]=dp[k][i]+1。记录最大值。
时间复杂度：O(n²)
空间复杂度：O(n²)
"""


def lenLongestFibSubseq(arr: list[int]) -> int:
    n = len(arr)
    # 建立值到索引的映射，便于 O(1) 查找某个值是否存在及其位置
    index_map: dict[int, int] = {val: i for i, val in enumerate(arr)}

    # dp[i][j] 表示以 arr[i] 和 arr[j] 结尾的斐波那契子序列的最大长度，最少为 2
    dp = [[2] * n for _ in range(n)]
    max_len = 0

    # j 从 1 到 n-1，i 从 0 到 j-1（保证 i < j）
    for j in range(1, n):
        for i in range(j):
            # 斐波那契条件：arr[i] + arr[j] = 下一个数
            # 反向查找前驱：target = arr[j] - arr[i]
            target = arr[j] - arr[i]
            # target 必须小于 arr[i]（因为序列递增）且存在于数组中
            if target < arr[i] and target in index_map:
                k = index_map[target]
                # 以 arr[k], arr[i], arr[j] 构成更长的斐波那契子序列
                dp[i][j] = dp[k][i] + 1
                max_len = max(max_len, dp[i][j])

    # 序列长度至少为 3 才有效
    return max_len if max_len >= 3 else 0


if __name__ == "__main__":
    # 示例：[1,2,3,4,5,6,7,8] → 输出: 5（[1,2,3,5,8]）
    assert lenLongestFibSubseq([1, 2, 3, 4, 5, 6, 7, 8]) == 5
    # 示例：[1,3,7,11,12,14,18] → 输出: 3（[1,11,12] 或 [3,7,11] 等）
    assert lenLongestFibSubseq([1, 3, 7, 11, 12, 14, 18]) == 3
