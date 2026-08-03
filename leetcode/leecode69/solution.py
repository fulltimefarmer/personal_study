"""
考点: Math, Binary Search
题目: Sqrt(x)（x 的平方根）
题目描述: 计算非负整数 x 的算术平方根，只保留整数部分，不允许使用内置指数函数。
示例: x = 4 -> 2
示例: x = 8 -> 2
思路: 二分查找。在 [1, x] 范围内找最大的 mid 使得 mid * mid <= x。
      用除法 mid <= x/mid 避免溢出。
时间复杂度: O(log x)
空间复杂度: O(1)
"""


def mySqrt(x: int) -> int:
    if x < 2:
        return x  # 0 和 1 的平方根就是自身

    # 平方根不会超过 x // 2（当 x >= 2 时）
    left = 1
    right = x // 2  # // 是 Python 的整数除法（向负无穷取整）
    result = 0

    # 二分查找: 循环直到搜索空间为空
    while left <= right:
        # (left + right) // 2 求中间值，等价于 Math.floor((left + right) / 2)
        # Python 的整数不会溢出，但用 // 更清晰
        mid = (left + right) // 2

        # 用除法代替乘法判断: mid <= x / mid <-> mid * mid <= x
        # 这样避免 mid * mid 可能的整数溢出（Python int 无此问题，但保持习惯）
        if mid <= x / mid:
            result = mid  # mid 是候选答案
            left = mid + 1  # 尝试找更大的
        else:
            right = mid - 1  # mid 太大，缩小范围

    return result


if __name__ == "__main__":
    assert mySqrt(4) == 2
    assert mySqrt(8) == 2
    assert mySqrt(0) == 0
    assert mySqrt(1) == 1
    assert mySqrt(2) == 1
    assert mySqrt(15) == 3
