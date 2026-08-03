/**
 * 考点：String, Dynamic Programming, Backtracking
 * 题目：Generate Parentheses（括号生成）
 * 题目描述：生成 n 对括号的所有有效组合。
 * 示例：n = 3 => ["((()))","(()())","(())()","()(())","()()()"]
 * 思路：回溯法，维护已使用的左右括号数，open < n 时加左括号，close < open 时加右括号
 * 时间复杂度：O(4^n / sqrt(n))
 * 空间复杂度：O(n)
 */
function generateParenthesis(n: number): string[] {
    const result: string[] = [];

    function backtrack(current: string, open: number, close: number): void {
        if (current.length === 2 * n) {
            result.push(current);
            return;
        }

        if (open < n) {
            backtrack(current + "(", open + 1, close);
        }

        if (close < open) {
            backtrack(current + ")", open, close + 1);
        }
    }

    backtrack("", 0, 0);
    return result;
}
export { generateParenthesis };
