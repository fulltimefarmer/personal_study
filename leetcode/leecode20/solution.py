"""
考点：字符串、栈
题目：Valid Parentheses（有效的括号）
思路：使用栈匹配括号，遇到左括号压入栈中，遇到右括号检查栈顶是否匹配，最后检查栈是否为空
时间复杂度：O(n)
空间复杂度：O(n)
"""

def isValid(s: str) -> bool:
    stack: list[str] = []  # 使用列表模拟栈（append 入栈，pop 出栈）

    # 右括号到左括号的映射字典
    pairs: dict[str, str] = {
        ")": "(",
        "]": "[",
        "}": "{",
    }

    for ch in s:
        # 使用 match-case（Python 3.10+ 的结构模式匹配）处理字符类型
        # 也可以用 if ch in pairs 判断是否为右括号
        match ch:
            case ")":
                # 栈为空或栈顶不匹配则无效
                if not stack or stack.pop() != "(":
                    return False
            case "]":
                if not stack or stack.pop() != "[":
                    return False
            case "}":
                if not stack or stack.pop() != "{":
                    return False
            case _:  # _ 是通配符模式，匹配任意值（这里对应左括号）
                stack.append(ch)

    # 最终栈应为空，否则有未闭合的左括号
    return len(stack) == 0

if __name__ == "__main__":
    assert isValid("()") == True
    assert isValid("()[]{}") == True
    assert isValid("(]") == False
    assert isValid("([])") == True
    assert isValid("]") == False
    print("全部通过 ✓")
