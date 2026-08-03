/**
 * 考点：栈、设计
 * 题目：Min Stack（最小栈）
 * 题目描述：实现一个能在 O(1) 时间内获取最小值的栈。
 *   示例：push(-2) push(0) push(-3) getMin() → -3, pop() top() → 0, getMin() → -2
 * 思路：辅助栈。额外维护一个 minStack，与主栈同步，记录每个位置对应的最小值。
 * 时间复杂度：O(1)
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
