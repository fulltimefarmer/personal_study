/**
 * 考点：栈、数组、数学
 * 题目：Evaluate Reverse Polish Notation（逆波兰表达式求值）
 * 题目描述：计算逆波兰表达式（后缀表达式）的值。运算符包括 +, -, *, /，除法向零截断。
 *   示例：tokens = ["2","1","+","3","*"] → 9
 * 思路：栈。遇到数字入栈，遇到运算符弹出两个操作数计算后入栈。
 *   注意减法和除法的操作数顺序（后弹出的是左操作数）。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */

function evalRPN(tokens: string[]): number {
  const stack: number[] = [];

  for (const token of tokens) {
    if (token === '+' || token === '-' || token === '*' || token === '/') {
      const b = stack.pop()!;
      const a = stack.pop()!;
      switch (token) {
        case '+':
          stack.push(a + b);
          break;
        case '-':
          stack.push(a - b);
          break;
        case '*':
          stack.push(a * b);
          break;
        case '/':
          stack.push(Math.trunc(a / b));
          break;
      }
    } else {
      stack.push(Number(token));
    }
  }

  return stack[0];
}

export { evalRPN };
