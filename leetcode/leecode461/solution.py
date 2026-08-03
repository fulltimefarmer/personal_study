"""
考点：位运算
题目：Hamming Distance（汉明距离）
题目描述：两个整数之间的汉明距离是两个数字对应二进制位不同的位置的数目。给定 x 和 y，计算汉明距离。
思路：计算 x ^ y，然后使用 Brian Kernighan 算法统计异或结果中 1 的个数。每次 n & (n-1) 会消除最低位的 1。
时间复杂度：O(log n)
空间复杂度：O(1)
"""


def hammingDistance(x: int, y: int) -> int:
    # 异或运算：相同位为 0，不同位为 1，统计结果中 1 的个数即为汉明距离
    xor = x ^ y
    distance = 0
    # Brian Kernighan 算法：n & (n-1) 每次消除最低位的 1，直到 xor 变为 0
    while xor != 0:
        xor &= xor - 1
        distance += 1
    return distance


if __name__ == "__main__":
    # 示例：x=1(0001), y=4(0100)，第 2 位和第 4 位不同 → 输出: 2
    assert hammingDistance(1, 4) == 2
    # 示例：x=3(0011), y=1(0001)，只有第 2 位不同 → 输出: 1
    assert hammingDistance(3, 1) == 1
