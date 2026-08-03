"""
考点：栈、数学、字符串
题目：Basic Calculator II（基本计算器 II）
思路：无栈优化——维护 lastNum 和 res。遇到数字累积；遇到运算符：
      +/- 将 lastNum 加入 res；* / 更新 lastNum。最后将 lastNum 加入 res 返回。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def calculateII(s: str) -> int:
    res = 0      # 累计结果
    last_num = 0 # 上一个"待加入"的数字（* / 场景下暂不加入 res）
    num = 0      # 当前解析的数字
    op = "+"     # 当前的运算符，初始为 '+' 处理第一个数字

    for i, ch in enumerate(s):
        # 解析数字：连续数字字符累积
        if "0" <= ch <= "9":
            num = num * 10 + (ord(ch) - 48)

        # 遇到运算符或到达字符串末尾时，处理上一个运算符
        # Python 3.12 的 match-case 在这里不适合（需要基于上一个 op 做判断，
        # 且条件判断涉及多种模式+字符串值匹配，用 if/elif 更清晰）
        if (ch < "0" or ch > "9") and ch != " " or i == len(s) - 1:
            if op == "+":
                res += last_num   # 上一个待加入数字确定加入
                last_num = num    # 当前数字成为新的待加入数字
            elif op == "-":
                res += last_num
                last_num = -num   # 减法作为负数保存
            elif op == "*":
                last_num *= num   # 乘法和上一个待加入数字直接相乘
            elif op == "/":
                # Python 的 // 是地板除，对于负数结果会向下取整
                # 需要使用 int(last_num / num) 实现向零取整（truncate）
                last_num = int(last_num / num)

            op = ch   # 更新运算符为当前字符
            num = 0   # 重置数字解析器

    # 将最后一个待加入数字结算
    res += last_num
    return res


if __name__ == "__main__":
    # 示例 1: "3+2*2" → 7
    assert calculateII("3+2*2") == 7
    # 示例 2: " 3/2 " → 1 (向零取整)
    assert calculateII(" 3/2 ") == 1
    # 示例 3: " 3+5 / 2 " → 5
    assert calculateII(" 3+5 / 2 ") == 5
    print("全部测试通过")
