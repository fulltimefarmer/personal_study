/**
 * 考点：Array, Backtracking
 * 题目：Permutations（全排列）
 * 题目描述：返回数组的所有全排列。如 [1,2,3] → [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
 * 思路：回溯 + used数组标记已选元素。path长度等于nums长度时加入结果。
 * 时间复杂度：O(n × n!)
 * 空间复杂度：O(n)
 */
function permute(nums: number[]): number[][] {
    const result: number[][] = [];
    const used: boolean[] = new Array(nums.length).fill(false);

    function backtrack(path: number[]): void {
        if (path.length === nums.length) {
            result.push([...path]);
            return;
        }
        for (let i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.push(nums[i]);
            backtrack(path);
            path.pop();
            used[i] = false;
        }
    }

    backtrack([]);
    return result;
}

export { permute };
