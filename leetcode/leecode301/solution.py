"""
考点：BFS、字符串、回溯
题目：Remove Invalid Parentheses（删除无效的括号）—— LeetCode 301
题目描述：删除最少数量括号使字符串有效，返回所有可能结果
思路：BFS。逐层删除括号，每层检查是否有效，首次发现有效结果即停止。
时间复杂度：O(2^n)
空间复杂度：O(n × 2^n)
"""

from collections import deque


def removeInvalidParentheses(s: str) -> list[str]:
    """BFS 逐层删除括号，找到所有删除最少括号的有效字符串"""

    # 判断字符串中的括号是否有效（匹配）
    def is_valid(st: str) -> bool:
        count = 0
        for ch in st:
            if ch == "(":
                count += 1
            elif ch == ")":
                count -= 1
            # 任何时刻右括号多于左括号，说明无效
            if count < 0:
                return False
        return count == 0  # 最终左右括号数相等

    result: list[str] = []
    visited: set[str] = set()  # 记录已访问的字符串，避免重复 BFS
    # collections.deque 是双端队列，支持两端 O(1) 添加/弹出，比 list 更高效做队列
    queue: deque[str] = deque([s])
    visited.add(s)
    found = False  # 标记是否已找到有效结果（当前层找到后停止扩展下一层）

    while queue:
        # popleft() 从队列左端弹出，模拟 FIFO 队列
        current = queue.popleft()

        if is_valid(current):
            result.append(current)
            found = True  # 找到有效结果，当前层即为最少删除层

        if found:
            continue  # 不再扩展当前层的下一层

        # 枚举删除每个位置的一个括号，生成下一层候选
        for i in range(len(current)):
            if current[i] not in ("(", ")"):
                continue  # 跳过非括号字符
            # 字符串切片 [0:i] + [i+1:] 实现删除第 i 个字符
            nxt = current[:i] + current[i + 1:]
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    return result


if __name__ == "__main__":
    assert set(removeInvalidParentheses("()())()")) == {"(())()", "()()()"}
    assert set(removeInvalidParentheses("(a)())()")) == {"(a())()", "(a)()()"}
    assert set(removeInvalidParentheses(")(")) == {""}
    assert set(removeInvalidParentheses("x(")) == {"x"}
    assert set(removeInvalidParentheses("))((")) == {""}
    print("所有断言通过！")
