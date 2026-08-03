/**
 * 考点：Backtracking
 * 题目：Combinations（组合）
 * 题目描述：给定 n 和 k，返回 [1, n] 中所有 k 个数的组合。
 * 示例：n = 4, k = 2 → [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
 * 思路：回溯。从 start 开始选数，避免重复。path 长度等于 k 时加入结果。
 *       剪枝优化：剩余数字不足时提前终止。
 * 时间复杂度：O(C(n, k) × k)
 * 空间复杂度：O(k)
 */
function combine(n: number, k: number): number[][] {
    const result: number[][] = [];
    const path: number[] = [];

    function backtrack(start: number): void {
        if (path.length === k) {
            result.push([...path]);
            return;
        }

        for (let i = start; i <= n - (k - path.length) + 1; i++) {
            path.push(i);
            backtrack(i + 1);
            path.pop();
        }
    }

    backtrack(1);
    return result;
}

export { combine };
