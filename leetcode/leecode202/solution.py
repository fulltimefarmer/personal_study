"""
考点：哈希表、数学、双指针
题目：Happy Number（快乐数）
思路：快慢指针（Floyd 判圈法）。快指针每次算两步，慢指针算一步，相遇时判是否为 1。
时间复杂度：O(log n)
空间复杂度：O(1)
"""


def isHappy(n: int) -> bool:
    def get_next(num: int) -> int:
        """计算 num 各位数字的平方和"""
        s = 0
        while num > 0:
            digit = num % 10       # 取个位数
            s += digit * digit     # 累加平方
            num //= 10             # 去掉个位
        return s

    slow = n                      # 慢指针
    fast = get_next(n)            # 快指针（领先一步）

    # Floyd 判圈：如果存在循环，快慢指针最终会相等
    while fast != 1 and slow != fast:
        slow = get_next(slow)              # 慢指针每次走一步
        fast = get_next(get_next(fast))    # 快指针每次走两步

    return fast == 1  # 循环结束时，如果快指针为 1 则是快乐数


if __name__ == "__main__":
    # n=19 → true (1^2+9^2=82→68→100→1)
    assert isHappy(19) is True
    # n=2 → false (进入循环 4→16→37→58→89→145→42→20→4)
    assert isHappy(2) is False
    print("全部测试通过")
