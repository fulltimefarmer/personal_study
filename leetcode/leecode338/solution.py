"""
考点：位运算、动态规划
题目：Counting Bits（比特位计数）—— LeetCode 338
题目描述：对 0 到 n 的每个数，计算二进制中 1 的个数
思路：DP 递推。dp[i] = dp[i >> 1] + (i & 1)
      即 i 的 popcount = i/2 的 popcount + i 的最低位。
时间复杂度：O(n)
空间复杂度：O(1)（不含结果数组）
"""

def countBits(n: int) -> list[int]:
    # dp[i] 表示数字 i 的二进制表示中 1 的个数
    dp = [0] * (n + 1)

    for i in range(1, n + 1):
        # i >> 1 等价于 i // 2（右移一位，去掉最低位）
        # i & 1 等价于 i % 2（与操作，获取最低位是 0 还是 1）
        # 例如 i=5(101): dp[5] = dp[2](10) + 1 = 1 + 1 = 2
        dp[i] = dp[i >> 1] + (i & 1)

    return dp


if __name__ == "__main__":
    assert countBits(2) == [0, 1, 1]
    assert countBits(5) == [0, 1, 1, 2, 1, 2]
    assert countBits(0) == [0]
    assert countBits(1) == [0, 1]
    assert countBits(8) == [0, 1, 1, 2, 1, 2, 2, 3, 1]
    print("所有断言通过！")
