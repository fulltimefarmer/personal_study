/**
 * 考点：Array, Hash Table
 * 题目：Two Sum（两数之和）
 * 题目描述：给定整数数组 nums 和目标值 target，找出和为 target 的两个数的下标。
 * 示例：nums = [2,7,11,15], target = 9 → [0,1]
 * 思路：遍历数组，用哈希表存储已遍历的值和下标。对每个元素查找 complement = target - nums[i] 是否在哈希表中。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function twoSum(nums: number[], target: number): number[] {
    const map = new Map<number, number>();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (map.has(complement)) {
            return [map.get(complement)!, i];
        }
        map.set(nums[i], i);
    }
    return [];
}

export { twoSum };
