/**
 * 考点：String, Stack
 * 题目：Valid Parentheses（有效的括号）
 * 题目描述：给定只包含 '()[]{}' 的字符串，判断括号是否有效闭合。
 * 示例：s = "()[]{}" => true
 * 思路：使用栈匹配，左括号入栈，右括号与栈顶匹配
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function isValid(s: string): boolean {
    const stack: string[] = [];
    const pairs: Record<string, string> = {
        ")": "(",
        "]": "[",
        "}": "{",
    };

    for (const char of s) {
        if (char in pairs) {
            if (stack.length === 0 || stack.pop() !== pairs[char]) {
                return false;
            }
        } else {
            stack.push(char);
        }
    }

    return stack.length === 0;
}
export { isValid };
