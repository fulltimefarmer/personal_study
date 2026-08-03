/**
 * 考点：栈、递归、字符串
 * 题目：Decode String（字符串解码）
 * 题目描述：编码规则 k[encoded_string]，解码还原字符串
 * 思路：双栈法。数字栈存重复次数，字符串栈存前缀。
 *       遇 '[' 压栈保存状态，遇 ']' 弹出栈顶拼接重复字符串。
 * 时间复杂度：O(S)，S 为解码后字符串长度
 * 空间复杂度：O(S)
 */
function decodeString(s: string): string {
    const numStack: number[] = [];
    const strStack: string[] = [];
    let currentStr = '';
    let currentNum = 0;

    for (const ch of s) {
        if (ch >= '0' && ch <= '9') {
            currentNum = currentNum * 10 + (ch.charCodeAt(0) - '0'.charCodeAt(0));
        } else if (ch === '[') {
            numStack.push(currentNum);
            strStack.push(currentStr);
            currentNum = 0;
            currentStr = '';
        } else if (ch === ']') {
            const repeat = numStack.pop()!;
            const prevStr = strStack.pop()!;
            currentStr = prevStr + currentStr.repeat(repeat);
        } else {
            currentStr += ch;
        }
    }

    return currentStr;
}

export { decodeString };
