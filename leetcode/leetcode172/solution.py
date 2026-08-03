"""
考点：数学
题目：Factorial Trailing Zeroes（阶乘后的零）
题目描述：计算 n! 的十进制表示中末尾零的个数。
  示例：n = 5, 5! = 120 → 1
思路：末尾零来自因子 10 = 2 × 5。阶乘中 2 的数量远多于 5，因此零的个数由 5 的个数决定。
  统计 n! 中包含多少个因子 5：n/5 + n/25 + n/125 + ...
时间复杂度：O(log_5 n)
空间复杂度：O(1)
"""


def trailingZeroes(n: int) -> int:
    # 关键：每个因子 5 贡献一个末尾零（因为 2 总是够用）
    count = 0
    while n > 0:
        n //= 5  # 相当于 n = n // 5，统计 n/5, n/25, n/125...
        count += n  # n // 5 表示 n! 中能被 5 整除的因子个数
    return count


if __name__ == "__main__":
    assert trailingZeroes(3) == 0  # 3! = 6
    assert trailingZeroes(5) == 1  # 5! = 120
    assert trailingZeroes(0) == 0  # 0! = 1
    assert trailingZeroes(25) == 6  # 25! 中 5 出现了 6 次
