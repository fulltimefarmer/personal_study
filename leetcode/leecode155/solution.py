"""
考点：Stack, Design
题目：Min Stack（最小栈）
题目描述：设计栈，支持 push/pop/top 和 O(1) 获取最小值。
示例：push(-2) push(0) push(-3) getMin()→-3 pop() top()→0 getMin()→-2
思路：辅助栈，同步存储当前最小值。push 时辅助栈压入 min(val, 辅助栈顶)。
时间复杂度：所有操作 O(1)
空间复杂度：O(n)
"""


class MinStack:
    def __init__(self):
        # 主栈：存储所有元素
        self.stack: list[int] = []
        # 辅助栈：与主栈同步，存储"到当前位置的最小值"
        # 这样 pop 时只需要同时弹出两个栈，getMin 只需取辅助栈栈顶
        self.min_stack: list[int] = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        # 如果辅助栈为空，最小值就是 val
        # 否则取 val 和当前最小值的较小者
        if not self.min_stack:
            self.min_stack.append(val)
        else:
            self.min_stack.append(min(val, self.min_stack[-1]))  # [-1] 取最后一个元素（栈顶）

    def pop(self) -> None:
        self.stack.pop()
        self.min_stack.pop()  # 同步弹出辅助栈

    def top(self) -> int:
        return self.stack[-1]  # list[-1] 是 Python 取最后一个元素的方式

    def getMin(self) -> int:
        return self.min_stack[-1]


if __name__ == "__main__":
    stack = MinStack()
    stack.push(-2)
    stack.push(0)
    stack.push(-3)
    assert stack.getMin() == -3  # 返回 -3
    stack.pop()
    assert stack.top() == 0       # 返回 0
    assert stack.getMin() == -2  # 返回 -2

    stack2 = MinStack()
    stack2.push(1)
    assert stack2.getMin() == 1
    stack2.push(2)
    assert stack2.getMin() == 1
