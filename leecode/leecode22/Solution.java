/**
 * 考点：Backtracking
 * 题目：Generate Parentheses
 * 题目描述：
 *   数字 n 代表生成括号的对数，请你设计一个函数，用于生成所有可能的并且有效的括号组合。
 *   示例 1：输入 n = 3，输出 ["((()))","(()())","(())()","()(())","()()()"]。
 *   示例 2：输入 n = 1，输出 ["()"]。
 *   提示：1 <= n <= 8。
 * 思路：
 *   1. 定义回溯函数 backtrack(result, current, open, close, n)，其中 current 为当前构造的 StringBuilder，open 和 close 分别表示已使用的左、右括号数量。
 *   2. 当 current.length() 等于 2 * n 时，说明已使用 n 对括号，将 current.toString() 加入结果并返回。
 *   3. 若 open < n，可以在 current 末尾追加 '('，然后递归调用 backtrack(...)，递归结束后删除末尾字符以恢复状态。
 *   4. 若 close < open，可以在 current 末尾追加 ')'，保证右括号数量始终不超过左括号，然后递归调用 backtrack(...)，同样回溯时删除末尾字符。
 *   5. 通过剪枝（close 不能超过 open）自动过滤掉无效组合，最终得到所有合法序列。
 * 算法：回溯（Backtracking）—— 在约束条件下逐步构造解，当满足条件时记录结果，否则剪枝并回退。
 * 时间复杂度：O(4^n / sqrt(n))，卡塔兰数级别
 * 空间复杂度：O(n)，递归栈空间
 */
class Solution {
    public java.util.List<String> generateParenthesis(int n) {
        java.util.List<String> result = new java.util.ArrayList<>();
        backtrack(result, new StringBuilder(), 0, 0, n);
        return result;
    }

    private void backtrack(java.util.List<String> result, StringBuilder current, int open, int close, int n) {
        if (current.length() == n * 2) {
            result.add(current.toString());
            return;
        }
        if (open < n) {
            current.append('(');
            backtrack(result, current, open + 1, close, n);
            current.deleteCharAt(current.length() - 1);
        }
        if (close < open) {
            current.append(')');
            backtrack(result, current, open, close + 1, n);
            current.deleteCharAt(current.length() - 1);
        }
    }
}
