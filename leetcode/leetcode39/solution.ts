/**
 * 考点：Array, Backtracking
 * 题目：Combination Sum（组合总和）
 * 题目描述：找出数组中所有和为目标值的组合，元素可重复使用。如 [2,3,6,7], 7 → [[2,2,3],[7]]
 * 思路：回溯，startIndex避免重复组合。元素可重复使用，递归时i不变。
 * 时间复杂度：O(n^(target/min))
 * 空间复杂度：O(target/min)
 */
function combinationSum(candidates: number[], target: number): number[][] {
    candidates.sort((a, b) => a - b);
    const result: number[][] = [];

    function backtrack(start: number, remain: number, path: number[]): void {
        if (remain === 0) {
            result.push([...path]);
            return;
        }
        for (let i = start; i < candidates.length; i++) {
            if (candidates[i] > remain) break;
            path.push(candidates[i]);
            backtrack(i, remain - candidates[i], path);
            path.pop();
        }
    }

    backtrack(0, target, []);
    return result;
}

export { combinationSum };
