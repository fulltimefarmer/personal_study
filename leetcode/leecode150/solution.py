"""
考点：Stack, Array, Math
题目：Evaluate Reverse Polish Notation（逆波兰表达式求值）
题目描述：计算逆波兰表达式（后缀表达式），加减乘除，除法向零截断。
示例 1：["2","1","+","3","*"]，输出 9（(2+1)*3）
示例 2：["4","13","5","/","+"]，输出 6（4+13/5）
示例 3：["10","6","9","3","+","-11","*","/","*","17","+","5","+"]，输出 22
思路：栈模拟，数字入栈，运算符弹出两个数计算后入栈。除法用 int() 向零截断。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def evalRPN(tokens: list[str]) -> int:
    stack: list[int] = []

    for token in tokens:
        # Python 3.10+ match-case 模式匹配
        match token:
            case "+":
                b: int = stack.pop()
                a: int = stack.pop()
                stack.append(a + b)
            case "-":
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            case "*":
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            case "/":
                b = stack.pop()
                a = stack.pop()
                # int(a / b) 向零截断（与 Java/TypeScript 的 Math.trunc 等效）
                # Python 的 // 是向下取整，不能用于此场景（负数的行为不同）
                stack.append(int(a / b))
            case _:
                # 默认情况：数字，直接入栈
                stack.append(int(token))

    return stack[0]


if __name__ == "__main__":
    assert evalRPN(["2", "1", "+", "3", "*"]) == 9
    assert evalRPN(["4", "13", "5", "/", "+"]) == 6
    assert evalRPN(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22
    assert evalRPN(["3", "11", "+", "5", "-"]) == 9
