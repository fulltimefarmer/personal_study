"""
考点：数学、动态规划
题目：Integer Break（整数拆分）—— LeetCode 343
题目描述：将 n 拆分为至少两个正整数的和，使乘积最大
思路：数学法。尽可能多拆出 3。
      如果 n <= 3 返回 n-1；否则统计 3 的个数，
      余 1 时拿出一个 3 和 1 组成 4，余 2 则乘 2。
时间复杂度：O(1)
空间复杂度：O(1)
"""

def integerBreak(n: int) -> int:
    # n <= 3 时的特殊处理：必须拆成至少两个数
    # n=2: 拆成 1+1，乘积 1
    # n=3: 拆成 1+2，乘积 2
    if n <= 3:
        return n - 1

    # 尽可能多地拆出 3（最优策略，因为 3 是最优因子）
    count3 = n // 3  # 可以拆出的 3 的个数
    remainder = n % 3  # 除以 3 的余数

    match remainder:
        case 0:
            # 恰好是 3 的倍数，全部拆成 3
            return 3 ** count3
        case 1:
            # 余 1：拿出一个 3 和 1 组成 4（3*1 < 4）
            # 例如 n=10: 3+3+4 而不是 3+3+3+1
            return 3 ** (count3 - 1) * 4
        case _:  # remainder == 2
            # 余 2：直接乘 2
            return 3 ** count3 * 2


if __name__ == "__main__":
    assert integerBreak(2) == 1   # 1+1
    assert integerBreak(3) == 2   # 1+2
    assert integerBreak(4) == 4   # 2+2
    assert integerBreak(10) == 36 # 3+3+4
    assert integerBreak(6) == 9   # 3+3
    assert integerBreak(7) == 12  # 3+4 → 不对，应该是 3+2+2 → 12
    assert integerBreak(8) == 18  # 3+3+2
    assert integerBreak(9) == 27  # 3+3+3
    print("所有断言通过！")
