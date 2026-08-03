"""
考点: Recursion, Math
题目: Pow(x, n)（Pow(x, n)）
题目描述: 实现 pow(x, n)，计算 x 的整数 n 次幂 x^n。
示例: x = 2.00000, n = 10 -> 1024.00000
示例: x = 2.00000, n = -2 -> 0.25000
思路: 快速幂（二分法）。n 为偶数时 x^n = (x^2)^(n/2)，奇数时 x^n = x * (x^2)^(n/2)。
      迭代实现避免栈溢出，处理 n 为负数时转 1/pow(x,-n)，注意 n = -2^31 的溢出问题。
时间复杂度: O(log n)
空间复杂度: O(1)
"""


def myPow(x: float, n: int) -> float:
    if n == 0:
        return 1.0

    # 处理负指数: x^(-n) = 1 / x^n
    if n < 0:
        x = 1 / x
        # Python 的 int 是无限精度的，不需要处理 -2^31 溢出
        # 但为与原 TS 逻辑保持一致，保留此处理
        n = -n

    result = 1.0
    current = x

    # 快速幂核心: 将指数按二进制拆分
    # 例: n=10(二进制1010), 则 x^10 = x^8 * x^2 = (x^2)^4 * x^2
    # n & 1 判断最低位是否为 1（奇数），相当于 n % 2 == 1
    # n >>= 1 等价于 n //= 2，右移一位
    while n > 0:
        if n & 1:
            result *= current
        current *= current  # 底数平方: x, x^2, x^4, x^8, ...
        n >>= 1  # n //= 2 的位运算写法

    return result


if __name__ == "__main__":
    assert abs(myPow(2.00000, 10) - 1024.0) < 1e-9
    assert abs(myPow(2.10000, 3) - 9.261) < 1e-9
    assert abs(myPow(2.00000, -2) - 0.25) < 1e-9
    assert abs(myPow(1.0, -2147483648) - 1.0) < 1e-9  # 边界: 极大负指数
