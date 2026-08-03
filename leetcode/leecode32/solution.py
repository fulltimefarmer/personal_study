"""
考点：栈、字符串、动态规划
题目：Longest Valid Parentheses（最长有效括号）
思路：使用栈存储索引（初始压入 -1 作为基准），遇到 '(' 压入索引，遇到 ')' 弹栈后用当前索引减去栈顶计算长度
时间复杂度：O(n)
空间复杂度：O(n)
"""

def longestValidParentheses(s: str) -> int:
    # 栈中存储的是索引，而非字符本身
    # 初始压入 -1 作为计算长度的基准点（「最后一个未匹配的右括号」的索引）
    stack: list[int] = [-1]
    max_len = 0

    for i, ch in enumerate(s):
        if ch == "(":
            # 遇到左括号，将其索引入栈
            # 此时它可能成为未来有效括号子串的起始边界
            stack.append(i)
        else:
            # 遇到右括号，先弹出栈顶元素
            # 弹出的可能是匹配的左括号索引，也可能是未匹配的右括号索引
            stack.pop()

            if not stack:
                # 栈为空：说明当前右括号没有匹配的左括号
                # 将当前右括号的索引压入，作为下一个有效子串计算长度的新基准
                stack.append(i)
            else:
                # 栈非空：当前右括号与某个左括号完成匹配
                # 计算有效子串长度 = 当前索引 - 栈顶索引
                # 栈顶此时是「尚未匹配的最左边界」
                cur_len = i - stack[-1]
                max_len = max(max_len, cur_len)

    return max_len

if __name__ == "__main__":
    assert longestValidParentheses("(()") == 2
    assert longestValidParentheses(")()())") == 4
    assert longestValidParentheses("") == 0
    assert longestValidParentheses("()(())") == 6
    print("全部通过 ✓")
