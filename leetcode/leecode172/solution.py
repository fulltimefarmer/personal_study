"""
考点：数学
题目：Factorial Trailing Zeroes（阶乘后的零）
思路：尾随零由因子 10=2×5 产生，2 的数量总是多于 5，因此只需计算因子 5 的数量。
      不断将 n 除以 5，累加商，即 n/5 + n/25 + n/125 + ...
时间复杂度：O(log₅ n)
空间复杂度：O(1)
"""


def trailingZeroes(n: int) -> int:
    count = 0
    # 不断除以 5 并累加，统计 n! 中因子 5 的个数
    while n >= 5:
        n //= 5  # Python 3 中 // 是地板除
        count += n
    return count


if __name__ == "__main__":
    # 示例: n=5 → 1 (5!=120, 末尾 1 个零)
    assert trailingZeroes(5) == 1
    # 示例: n=3 → 0 (3!=6, 末尾无零)
    assert trailingZeroes(3) == 0
    # 示例: n=0 → 0
    assert trailingZeroes(0) == 0
    print("全部测试通过")
