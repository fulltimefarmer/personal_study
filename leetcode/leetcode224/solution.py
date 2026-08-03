"""
考点：栈、数学、字符串
题目：Basic Calculator（基本计算器）
题目描述：实现基本计算器，计算字符串表达式 s 的值。支持 +, -, (, ) 和空格。
  示例：s = "(1+(4+5+2)-3)+(6+8)" → 23
思路：栈模拟。遍历字符串，用 sign 记录当前符号（1 或 -1），num 累计当前数字。
  遇到 '(' 时将当前结果和符号压栈，开始新的子表达式计算。
  遇到 ')' 时，子表达式结果乘以栈顶符号再加到栈顶结果。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def calculate(s: str) -> int:
    stack: list[int] = []  # 栈：存储遇到 '(' 时的结果和符号
    result = 0  # 当前子表达式的结果
    sign = 1  # 当前符号：1 表示正，-1 表示负
    num = 0  # 当前正在读取的数字
    i = 0
    n = len(s)

    while i < n:
        ch = s[i]

        if ch.isdigit():  # 连续数字字符，累计为完整数字
            num = 0
            while i < n and s[i].isdigit():
                num = num * 10 + int(s[i])
                i += 1
            result += sign * num  # 将数字按符号加到结果
            continue  # 注意：内层 while 已经移动了 i，需要 continue

        match ch:
            case "+":
                sign = 1  # 设置下一个数字的符号为正
            case "-":
                sign = -1  # 设置下一个数字的符号为负
            case "(":  # 遇到左括号，压入当前结果和符号，重置状态
                stack.append(result)
                stack.append(sign)
                result = 0  # 重置结果，开始括号内的子表达式
                sign = 1  # 重置符号
            case ")":  # 遇到右括号，计算结果：栈内结果 + 符 * 括号内结果
                result = stack.pop() * result + stack.pop()
                # stack.pop() 先弹出 sign，再弹出之前的结果
            case _:
                pass  # 忽略空格

        i += 1

    return result


if __name__ == "__main__":
    assert calculate("1 + 1") == 2
    assert calculate(" 2-1 + 2 ") == 3
    assert calculate("(1+(4+5+2)-3)+(6+8)") == 23
    assert calculate("-(2+3)") == -5
    assert calculate("0") == 0
