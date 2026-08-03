"""
考点：位运算、分治
题目：Number of 1 Bits（位1的个数）
思路：n & (n-1) 消除最低位的 1，计数直到 n 为 0。
时间复杂度：O(k)，k 为 1 的个数
空间复杂度：O(1)
"""


def hammingWeight(n: int) -> int:
    count = 0
    # n & (n-1) 消除最低位的 1，直到 n 变为 0
    while n != 0:
        n &= n - 1  # Python 中的 n &= n - 1 等价于 n = n & (n - 1)
        count += 1
    return count


if __name__ == "__main__":
    # n = 11 (二进制: 1011) → 3 个 1
    assert hammingWeight(11) == 3
    # n = 128 (二进制: 10000000) → 1 个 1
    assert hammingWeight(128) == 1
    # n = 4294967293 (二进制: 11111111111111111111111111111101) → 31 个 1
    assert hammingWeight(4294967293) == 31
    print("全部测试通过")
