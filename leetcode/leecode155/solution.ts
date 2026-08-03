/**
 * 考点：Stack, Design
 * 题目：Min Stack（最小栈）
 * 题目描述：设计栈，支持 push/pop/top 和 O(1) 获取最小值。
 * 示例：push(-2) push(0) push(-3) getMin()→-3 pop() top()→0 getMin()→-2
 * 思路：辅助栈，同步存储当前最小值。push 时辅助栈压入 min(val, 辅助栈顶)。
 * 时间复杂度：所有操作 O(1)
 * 空间复杂度：O(n)
 */
class MinStack {
    private stack: number[];
    private minStack: number[];

    constructor() {
        this.stack = [];
        this.minStack = [];
    }

    push(val: number): void {
        this.stack.push(val);
        if (this.minStack.length === 0) {
            this.minStack.push(val);
        } else {
            this.minStack.push(Math.min(val, this.minStack[this.minStack.length - 1]));
        }
    }

    pop(): void {
        this.stack.pop();
        this.minStack.pop();
    }

    top(): number {
        return this.stack[this.stack.length - 1];
    }

    getMin(): number {
        return this.minStack[this.minStack.length - 1];
    }
}

export { MinStack };
