/**
 * 考点：Stack
 * 题目：Valid Parentheses
 * 题目描述：
 *   给定一个只包括 '('、')'、'{'、'}'、'['、']' 的字符串 s，判断字符串是否有效。
 *   有效字符串需满足：
 *     1) 左括号必须用相同类型的右括号闭合。
 *     2) 左括号必须以正确的顺序闭合。
 *     3) 每个右括号都有一个对应的相同类型的左括号。
 *   示例 1：输入 s = "()"，输出 true。
 *   示例 2：输入 s = "()[]{}"，输出 true。
 *   示例 3：输入 s = "(]"，输出 false。
 *   示例 4：输入 s = "([])"，输出 true。
 *   提示：1 <= s.length <= 10^4，s 仅由括号 '()[]{}' 组成。
 * 思路：
 *   1. 准备一个栈 stack，并建立右括号到左括号的映射 map（')'->'('、']'->'['、'}'->'{'）。
 *   2. 遍历字符串中的每个字符 c：
 *      a) 若 c 是左括号，直接将其压入栈中。
 *      b) 若 c 是右括号，检查栈是否为空，以及栈顶元素是否等于 map[c]；若不匹配，立即返回 false。
 *      c) 若匹配，则弹出栈顶元素，继续处理下一个字符。
 *   3. 遍历结束后，若栈为空，说明所有括号都正确匹配，返回 true；否则返回 false。
 * 数据结构：栈（Stack）—— 后进先出（LIFO），用于记录最近未匹配的左括号。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function isValid(s: string): boolean {
    const stack: string[] = [];
    const map: Record<string, string> = { ')': '(', ']': '[', '}': '{' };
    for (const c of s) {
        if (c === '(' || c === '[' || c === '{') {
            stack.push(c);
        } else if (stack.length === 0 || stack[stack.length - 1] !== map[c]) {
            return false;
        } else {
            stack.pop();
        }
    }
    return stack.length === 0;
}
