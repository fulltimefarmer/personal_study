"""
考点: Array, Math
题目: Plus One（加一）
题目描述: 给定由整数数组表示的非负整数，加一后返回新的数组。
示例: digits = [1,2,3] -> [1,2,4]
示例: digits = [9] -> [1,0]
思路: 从末尾向前遍历，若 digits[i] < 9 则加一返回；若为 9 则置零并进位。
      若遍历完所有位都是 9，则在开头插入 1。
时间复杂度: O(n)
空间复杂度: O(1)（最坏 O(n)，当全为 9 时）
"""


def plusOne(digits: list[int]) -> list[int]:
    # range(len(digits) - 1, -1, -1): 从最后一个索引递减到 0
    # 第三个参数 -1 表示步长为 -1（倒序）
    for i in range(len(digits) - 1, -1, -1):
        if digits[i] < 9:
            # 当前位小于 9 时，直接加一并返回，不会有进位
            digits[i] += 1
            return digits
        # 当前位为 9，加一后变为 0，进位到前一位
        digits[i] = 0

    # 执行到这里说明所有位都是 9（如 999 -> 1000）
    # list.insert(0, val) 在列表开头插入元素，时间复杂度 O(n)
    digits.insert(0, 1)
    return digits


if __name__ == "__main__":
    assert plusOne([1, 2, 3]) == [1, 2, 4]
    assert plusOne([4, 3, 2, 1]) == [4, 3, 2, 2]
    assert plusOne([9]) == [1, 0]
    assert plusOne([9, 9, 9]) == [1, 0, 0, 0]
