"""
考点：栈、递归、数学、字符串
题目：Basic Calculator（基本计算器）
思路：栈处理括号。维护当前结果 res 和符号 sign。遇到 '(' 压栈当前 res 和 sign；
      遇到 ')' 弹出栈顶结合。处理一元负号：默认符号 1，遇到 '-' 时符号置 -1。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def calculate(s: str) -> int:
    res = 0      # 当前层级的结果
    sign = 1     # 当前符号：1 表示正，-1 表示负
    num = 0      # 当前解析的数字
    stack: list[tuple[int, int]] = []  # 栈中存储 (之前的res, 之前的sign)

    for ch in s:
        if "0" <= ch <= "9":
            # 累积数字：处理多位数
            num = num * 10 + (ord(ch) - 48)
        elif ch == "+":
            # 遇到运算符，将之前累积的数字用当前符号加入结果
            res += sign * num
            num = 0
            sign = 1
        elif ch == "-":
            res += sign * num
            num = 0
            sign = -1  # 符号置为负
        elif ch == "(":
            # 遇到左括号，将当前结果和符号压栈，重置当前层级
            stack.append((res, sign))
            res = 0
            sign = 1
        elif ch == ")":
            # 遇到右括号，先结算括号内最后一个数字
            res += sign * num
            num = 0
            # 弹出栈顶的 (外层结果, 外层符号)
            prev_res, prev_sign = stack.pop()
            # 外层结果 += 外层符号 × 括号内结果
            res = prev_res + prev_sign * res

    # 处理最后一个数字
    res += sign * num
    return res


if __name__ == "__main__":
    # 示例 1: "1 + 1" → 2
    assert calculate("1 + 1") == 2
    # 示例 2: " 2-1 + 2 " → 3
    assert calculate(" 2-1 + 2 ") == 3
    # 示例 3: "(1+(4+5+2)-3)+(6+8)" → 23
    assert calculate("(1+(4+5+2)-3)+(6+8)") == 23
    print("全部测试通过")
