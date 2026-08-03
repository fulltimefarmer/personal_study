/**
 * 考点：Array, Backtracking
 * 题目：Permutations（全排列）
 * 题目描述：给定不含重复数字的数组，返回所有可能的全排列。
 * 示例：nums = [1,2,3] => [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
 * 思路：回溯法，使用 used 数组标记已使用的元素，构建所有排列
 * 时间复杂度：O(n * n!)
 * 空间复杂度：O(n)
 */
function permute(nums: number[]): number[][] {
    const result: number[][] = [];
    const used: boolean[] = Array.from({ length: nums.length }, () => false);

    function backtrack(current: number[]): void {
        if (current.length === nums.length) {
            result.push([...current]);
            return;
        }

        for (let i = 0; i < nums.length; i++) {
            if (used[i]) continue;

            used[i] = true;
            current.push(nums[i]);
            backtrack(current);
            current.pop();
            used[i] = false;
        }
    }

    backtrack([]);
    return result;
}
export { permute };
