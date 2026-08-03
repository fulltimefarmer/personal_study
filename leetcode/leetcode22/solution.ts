/**
 * 考点：String, Dynamic Programming, Backtracking
 * 题目：Generate Parentheses（括号生成）
 * 题目描述：生成所有有效的n对括号组合。如 n=3 → ["((()))","(()())","(())()","()(())","()()()"]
 * 思路：回溯，维护open和close计数。open<n时可加'(', close<open时可加')'。
 * 时间复杂度：O(4^n / √n)
 * 空间复杂度：O(n)
 */
function generateParenthesis(n: number): string[] {
    const result: string[] = [];

    function backtrack(open: number, close: number, path: string): void {
        if (path.length === 2 * n) {
            result.push(path);
            return;
        }
        if (open < n) {
            backtrack(open + 1, close, path + '(');
        }
        if (close < open) {
            backtrack(open, close + 1, path + ')');
        }
    }

    backtrack(0, 0, '');
    return result;
}

export { generateParenthesis };
