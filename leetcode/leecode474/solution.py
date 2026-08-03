"""
考点：数组, 字符串, 动态规划
题目：Ones and Zeroes（一和零）
题目描述：给定二进制字符串数组 strs 和两个整数 m 和 n。找出 strs 的最大子集的大小，该子集中最多有 m 个 0 和 n 个 1。
思路：二维 0-1 背包。dp[j][k] 表示使用 j 个 0 和 k 个 1 时最多可选的字符串数。对每个字符串统计 0 和 1 的数量，倒序更新 dp。
时间复杂度：O(L * m * n)
空间复杂度：O(m * n)
"""


def findMaxForm(strs: list[str], m: int, n: int) -> int:
    # 初始化二维 dp 数组，dp[j][k] 表示用 j 个 0、k 个 1 时的最大字符串数
    # 使用列表推导式创建 (m+1) x (n+1) 的二维数组，初始值为 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for s in strs:
        # 统计当前字符串中 0 和 1 的个数
        zeros = s.count("0")
        ones = len(s) - zeros  # 总长度减去 0 的个数即为 1 的个数

        # 0-1 背包倒序遍历，确保每个字符串只被使用一次
        # range 的步长为 -1 表示递减
        for j in range(m, zeros - 1, -1):
            for k in range(n, ones - 1, -1):
                # 选或不选：dp[j][k] 不变，或者选当前字符串：dp[j-zeros][k-ones] + 1
                dp[j][k] = max(dp[j][k], dp[j - zeros][k - ones] + 1)

    return dp[m][n]


if __name__ == "__main__":
    # 示例：strs=["10","0001","111001","1","0"], m=5, n=3 → 输出: 4
    assert findMaxForm(["10", "0001", "111001", "1", "0"], 5, 3) == 4
    # 示例：strs=["10","0","1"], m=1, n=1 → 输出: 2
    assert findMaxForm(["10", "0", "1"], 1, 1) == 2
