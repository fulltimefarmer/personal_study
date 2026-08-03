/**
 * 考点：Stack, String, Dynamic Programming
 * 题目：Longest Valid Parentheses（最长有效括号）
 * 题目描述：找出只包含 '(' 和 ')' 的字符串中最长有效括号子串的长度。
 * 示例：s = ")()())" => 4（"()()"）
 * 思路：用栈记录索引，遇到 '(' 压索引，遇到 ')' 弹栈后计算长度
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function longestValidParentheses(s: string): number {
    const stack: number[] = [-1];
    let maxLen = 0;

    for (let i = 0; i < s.length; i++) {
        if (s[i] === "(") {
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
