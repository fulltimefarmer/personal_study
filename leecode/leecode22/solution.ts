/**
 * 考点：Backtracking
 * 题目：Generate Parentheses
 * 题目描述：
 *   数字 n 代表生成括号的对数，请你设计一个函数，用于生成所有可能的并且有效的括号组合。
 *   示例 1：输入 n = 3，输出 ["((()))","(()())","(())()","()(())","()()()"]。
 *   示例 2：输入 n = 1，输出 ["()"]。
 *   提示：1 <= n <= 8。
 * 思路：
 *   1. 定义回溯函数 backtrack(current, open, close)，其中 current 为当前构造的括号串，open 和 close 分别表示已使用的左、右括号数量。
 *   2. 当 current.length 等于 2 * n 时，说明已使用 n 对括号，将 current 加入结果并返回。
 *   3. 若 open < n，可以在当前串后添加 '('，然后递归调用 backtrack(current + '(', open + 1, close)。
 *   4. 若 close < open，可以在当前串后添加 ')'，保证右括号数量始终不超过左括号，然后递归调用 backtrack(current + ')', open, close + 1)。
 *   5. 通过剪枝（close 不能超过 open）自动过滤掉无效组合，最终得到所有合法序列。
 * 算法：回溯（Backtracking）—— 在约束条件下逐步构造解，当满足条件时记录结果，否则剪枝并回退。
 * 时间复杂度：O(4^n / sqrt(n))，卡塔兰数级别
 * 空间复杂度：O(n)，递归栈空间
 */
function generateParenthesis(n: number): string[] {
    const result: string[] = [];
    function backtrack(current: string, open: number, close: number) {
        if (current.length === n * 2) {
            result.push(current);
            return;
        }
        if (open < n) {
            backtrack(current + '(', open + 1, close);
        }
        if (close < open) {
            backtrack(current + ')', open, close + 1);
        }
    }
    backtrack('', 0, 0);
    return result;
}
