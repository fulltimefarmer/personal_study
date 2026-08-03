/**
 * 考点：栈、数学、字符串
 * 题目：Basic Calculator II（基本计算器 II）
 * 题目描述：计算包含 +、-、*、/ 的表达式（无括号）。s="3+2*2" 输出 7，s=" 3/2 " 输出 1
 * 思路：无栈优化——维护 lastNum 和 res。遇到数字累积；遇到运算符：+/- 将 lastNum 加入 res；* / 更新 lastNum。
 *       最后将 lastNum 加入 res 返回。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function calculateII(s: string): number {
    let res = 0;
    let lastNum = 0;
    let num = 0;
    let op = '+';

    for (let i = 0; i < s.length; i++) {
        const ch = s[i];

        if (ch >= '0' && ch <= '9') {
            num = num * 10 + (ch.charCodeAt(0) - 48);
        }

        if ((ch < '0' || ch > '9') && ch !== ' ' || i === s.length - 1) {
            if (op === '+') {
                res += lastNum;
                lastNum = num;
            } else if (op === '-') {
                res += lastNum;
                lastNum = -num;
            } else if (op === '*') {
                lastNum *= num;
            } else if (op === '/') {
                lastNum = Math.trunc(lastNum / num);
            }
            op = ch;
            num = 0;
        }
    }

    res += lastNum;
    return res;
}
export { calculateII };
