/**
 * 考点：Bit Manipulation, Array, Backtracking
 * 题目：Subsets（子集）
 * 题目描述：给定互不相同的整数数组 nums，返回所有可能子集（幂集）。
 * 示例：nums = [1,2,3] → [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
 * 思路：回溯。对每个元素选或不选，递归树上的每个节点都是一个子集。
 *       也可用位运算枚举所有 mask。
 * 时间复杂度：O(n × 2^n)
 * 空间复杂度：O(n)
 */
function subsets(nums: number[]): number[][] {
    const result: number[][] = [];
    const path: number[] = [];

    function backtrack(index: number): void {
        result.push([...path]);

        for (let i = index; i < nums.length; i++) {
            path.push(nums[i]);
            backtrack(i + 1);
            path.pop();
        }
    }

    backtrack(0);
    return result;
}

export { subsets };
