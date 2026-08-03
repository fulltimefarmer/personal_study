/**
 * 考点：Array, Hash Table
 * 题目：First Missing Positive（缺失的第一个正数）
 * 题目描述：找数组中缺失的最小正整数。如 [3,4,-1,1] → 2
 * 思路：原地哈希。将值x(1..n)交换到索引x-1处。最后遍历找第一个nums[i] !== i+1的位置。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function firstMissingPositive(nums: number[]): number {
    const n = nums.length;

    for (let i = 0; i < n; i++) {
        while (nums[i] > 0 && nums[i] <= n && nums[nums[i] - 1] !== nums[i]) {
            const correctIdx = nums[i] - 1;
            [nums[i], nums[correctIdx]] = [nums[correctIdx], nums[i]];
        }
    }

    for (let i = 0; i < n; i++) {
        if (nums[i] !== i + 1) {
            return i + 1;
        }
    }

    return n + 1;
}

export { firstMissingPositive };
