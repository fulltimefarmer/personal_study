/**
 * 考点：Array, Backtracking
 * 题目：Combination Sum（组合总和）
 * 题目描述：找出 candidates 中所有可以使数字和为 target 的组合，数字可重复使用。
 * 示例：candidates = [2,3,6,7], target = 7 => [[2,2,3],[7]]
 * 思路：回溯法，从 start 开始遍历，允许重复选择同一个元素
 * 时间复杂度：O(N^(T/M))
 * 空间复杂度：O(T/M)
 */
function combinationSum(candidates: number[], target: number): number[][] {
    const result: number[][] = [];

    function backtrack(start: number, current: number[], remaining: number): void {
        if (remaining < 0) return;
        if (remaining === 0) {
            result.push([...current]);
            return;
        }

        for (let i = start; i < candidates.length; i++) {
            current.push(candidates[i]);
            backtrack(i, current, remaining - candidates[i]);
            current.pop();
        }
    }

    backtrack(0, [], target);
    return result;
}
export { combinationSum };
