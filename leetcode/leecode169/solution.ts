/**
 * 考点：Array, Hash Table, Divide and Conquer, Counting, Sorting
 * 题目：Majority Element（多数元素）
 * 题目描述：找出现次数大于 n/2 的元素（多数元素一定存在）。
 * 示例 1：[3,2,3]，输出 3
 * 示例 2：[2,2,1,1,1,2,2]，输出 2
 * 思路：Boyer-Moore 投票算法。count=0 时更新候选，相等则 count++，不等则 count--。
 * 多数元素出现超过一半，最终 candidate 即为答案。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function majorityElement(nums: number[]): number {
    let candidate = nums[0];
    let count = 0;

    for (const num of nums) {
        if (count === 0) {
            candidate = num;
        }
        count += (num === candidate) ? 1 : -1;
    }

    return candidate;
}

export { majorityElement };
