/**
 * 考点：Array, Hash Table
 * 题目：First Missing Positive（缺失的第一个正数）
 * 题目描述：找出未排序整数数组中没有出现的最小正整数。
 * 示例：nums = [3,4,-1,1] => 2
 * 思路：原地哈希，将数组本身当哈希表，把值映射到对应下标并标记为负数
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function firstMissingPositive(nums: number[]): number {
    const n = nums.length;

    for (let i = 0; i < n; i++) {
        if (nums[i] <= 0 || nums[i] > n) {
            nums[i] = n + 1;
        }
    }

    for (let i = 0; i < n; i++) {
        const num = Math.abs(nums[i]);
        if (num <= n) {
            nums[num - 1] = -Math.abs(nums[num - 1]);
        }
    }

    for (let i = 0; i < n; i++) {
        if (nums[i] > 0) {
            return i + 1;
        }
    }

    return n + 1;
}
export { firstMissingPositive };
