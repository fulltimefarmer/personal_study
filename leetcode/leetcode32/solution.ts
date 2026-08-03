/**
 * 考点：Stack, String, Dynamic Programming
 * 题目：Longest Valid Parentheses（最长有效括号）
 * 题目描述：找最长有效括号子串长度。如 ")()())" → 4 ("()()")
 * 思路：栈底存最后一个未匹配的右括号索引，遇到')'时弹出栈顶，用当前索引减栈顶得长度。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function longestValidParentheses(s: string): number {
    const stack: number[] = [-1];
    let maxLen = 0;

    for (let i = 0; i < s.length; i++) {
        if (s[i] === '(') {
            stack.push(i);
        } else {
            stack.pop();
            if (stack.length === 0) {
                stack.push(i);
            } else {
                maxLen = Math.max(maxLen, i - stack[stack.length - 1]);
            }
        }
    }

    return maxLen;
}

export { longestValidParentheses };
