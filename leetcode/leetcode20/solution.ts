/**
 * 考点：String, Stack
 * 题目：Valid Parentheses（有效的括号）
 * 题目描述：判断括号字符串是否有效。如 "()[]{}" → true, "(]" → false
 * 思路：栈存储左括号，遇到右括号时检查栈顶匹配。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function isValid(s: string): boolean {
    const stack: string[] = [];
    const map: Record<string, string> = {
        ')': '(',
        '}': '{',
        ']': '[',
    };

    for (const ch of s) {
        if (ch in map) {
            if (stack.length === 0 || stack.pop() !== map[ch]) {
                return false;
            }
        } else {
            stack.push(ch);
        }
    }

    return stack.length === 0;
}

export { isValid };
