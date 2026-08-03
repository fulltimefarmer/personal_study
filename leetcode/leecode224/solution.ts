/**
 * 考点：栈、递归、数学、字符串
 * 题目：Basic Calculator（基本计算器）
 * 题目描述：计算包含 +、-、()、空格的表达式值。s="(1+(4+5+2)-3)+(6+8)" 输出 23
 * 思路：栈处理括号。维护当前结果 res 和符号 sign。遇到 '(' 压栈当前 res 和 sign；遇到 ')' 弹出栈顶结合。
 *       处理一元负号：默认符号 1，遇到 '-' 时符号置 -1。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function calculate(s: string): number {
    let res = 0;
    let sign = 1;
    let num = 0;
    const stack: [number, number][] = [];

    for (let i = 0; i < s.length; i++) {
        const ch = s[i];

        if (ch >= '0' && ch <= '9') {
            num = num * 10 + (ch.charCodeAt(0) - 48);
        } else if (ch === '+') {
            res += sign * num;
            num = 0;
            sign = 1;
        } else if (ch === '-') {
            res += sign * num;
            num = 0;
            sign = -1;
        } else if (ch === '(') {
            stack.push([res, sign]);
            res = 0;
            sign = 1;
        } else if (ch === ')') {
            res += sign * num;
            num = 0;
            const [prevRes, prevSign] = stack.pop()!;
            res = prevRes + prevSign * res;
        }
    }

    res += sign * num;
    return res;
}
export { calculate };
