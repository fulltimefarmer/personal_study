/**
 * 考点：Array, Hash Table
 * 题目：Two Sum（两数之和）
 * 题目描述：给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。
 * 示例：nums = [2,7,11,15], target = 9 => [0,1]
 * 思路：使用哈希表存储遍历过的元素和下标，对于每个元素检查 target - nums[i] 是否已在表中
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
