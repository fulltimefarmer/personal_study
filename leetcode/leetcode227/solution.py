"""
考点：栈、数学、字符串
题目：Basic Calculator II（基本计算器 II）
题目描述：实现基本计算器，计算字符串表达式 s，支持 +, -, *, / 和空格（无括号）。
  整数除法仅保留整数部分。
  示例：s = "3+2*2" → 7
思路：栈。遍历字符串，用 pre_sign 记录上一个运算符。
  遇到数字时根据 pre_sign 处理：
  - +：将 num 压栈
  - -：将 -num 压栈
  - *：弹出栈顶，乘以 num 后压回
  - /：弹出栈顶，除以 num（取整）后压回
  最后栈中所有数求和即为结果。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def calculate(s: str) -> int:
    stack: list[int] = []  # 存储待求和的数字
    num = 0  # 当前正在读取的数字
    pre_sign = "+"  # 上一个运算符，初始为 "+"
    # 遍历完字符串后需要处理最后一个数字，所以在末尾加一个哨兵符号
    s = s + "+"

    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)  # 累计多位数
        elif ch in "+-*/":
            # 遇到运算符时，根据 pre_sign 处理之前累计的 num
            match pre_sign:
                case "+":
                    stack.append(num)  # 加法：直接入栈
                case "-":
                    stack.append(-num)  # 减法：负数入栈
                case "*":
                    stack.append(stack.pop() * num)  # 乘法：弹出栈顶相乘后压回
                case "/":
                    # 整数除法向零截断：Python 的 // 向负无穷取整，负数时需要用 int() 修正
                    stack.append(int(stack.pop() / num))
            pre_sign = ch  # 更新当前运算符
            num = 0  # 重置 num

    return sum(stack)  # 栈中所有数求和


if __name__ == "__main__":
    assert calculate("3+2*2") == 7
    assert calculate(" 3/2 ") == 1
    assert calculate(" 3+5 / 2 ") == 5
    assert calculate("14-3/2") == 13
    assert calculate("0") == 0
