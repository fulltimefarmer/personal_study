/**
 * 考点：Stack, Array, Math
 * 题目：Evaluate Reverse Polish Notation（逆波兰表达式求值）
 * 题目描述：计算逆波兰表达式（后缀表达式），加减乘除，除法向零截断。
 * 示例 1：["2","1","+","3","*"]，输出 9（(2+1)*3）
 * 示例 2：["4","13","5","/","+"]，输出 6（4+13/5）
 * 示例 3：["10","6","9","3","+","-11","*","/","*","17","+","5","+"]，输出 22
 * 思路：栈模拟，数字入栈，运算符弹出两个数计算后入栈。除法用 Math.trunc。
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
                case '+': stack.push(a + b); break;
                case '-': stack.push(a - b); break;
                case '*': stack.push(a * b); break;
                case '/': stack.push(Math.trunc(a / b)); break;
            }
        } else {
            stack.push(Number(token));
        }
    }

    return stack[0];
}

export { evalRPN };
