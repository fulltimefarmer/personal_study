"""
考点：哈希表、数学、双指针
题目：Happy Number（快乐数）
题目描述：正整数 n，每次将各位数字平方求和得到新数，若最终得到 1 则是快乐数；若无限循环则不是。
  示例：n = 19 → true（1²+9²=82, 8²+2²=68, 6²+8²=100, 1²+0²+0²=1）
思路：使用快慢指针（Floyd 判圈）检测循环。
  如果 fast 遇到 1 则返回 True，如果 fast 和 slow 相遇且不为 1 说明进入死循环。
时间复杂度：O(log n)
空间复杂度：O(1)
"""


def isHappy(n: int) -> bool:
    def get_next(x: int) -> int:
        """计算 x 各位数字的平方和"""
        total = 0
        while x > 0:
            digit = x % 10  # 取个位数
            total += digit * digit
            x //= 10  # 去掉个位数
        return total

    # 快慢指针检测循环：类似链表判环
    slow = n
    fast = get_next(n)

    while fast != 1 and slow != fast:
        slow = get_next(slow)  # 慢指针走一步
        fast = get_next(get_next(fast))  # 快指针走两步

    return fast == 1  # 如果快指针到 1 说明是快乐数


if __name__ == "__main__":
    assert isHappy(19) is True
    assert isHappy(2) is False
    assert isHappy(1) is True
