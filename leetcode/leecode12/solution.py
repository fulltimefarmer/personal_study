"""
考点：哈希表、数学、字符串
题目：Integer to Roman（整数转罗马数字）
思路：贪心算法，预定义从大到小的罗马数字映射表（包含 4/9 的特殊规则），不断减去最大的可用值
时间复杂度：O(1)
空间复杂度：O(1)
"""

def intToRoman(num: int) -> str:
    # 预定义所有可能的值和对应符号，从大到小排列
    # 包含所有特殊规则：CM(900)、CD(400)、XC(90)、XL(40)、IX(9)、IV(4)
    # 这样就不需要单独处理 4 和 9 的特殊情况
    values: list[int] = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    symbols: list[str] = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]

    result: list[str] = []  # 使用列表收集结果片段
    remaining = num

    # 贪心：从大值到小值，每次尽可能多地减去当前值
    for i in range(len(values)):
        # while 循环：当前值可以被减去多次累加
        # 例如 num=3000 会循环三次减去 1000，产生 "MMM"
        while remaining >= values[i]:
            result.append(symbols[i])  # 追加对应罗马符号
            remaining -= values[i]

    # "".join() 高效地将列表拼接为字符串（比字符串 += 效率更高）
    return "".join(result)

if __name__ == "__main__":
    assert intToRoman(3749) == "MMMDCCXLIX"
    assert intToRoman(58) == "LVIII"
    assert intToRoman(1994) == "MCMXCIV"
    print("全部通过 ✓")
