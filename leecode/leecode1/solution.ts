/**
 * 考点：Hash Table
 * 题目：Two Sum
 * 题目描述：
 *   给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。
 *   你可以假设每种输入只会对应一个答案。但是，数组中同一个元素在答案里不能重复出现。
 *   你可以按任意顺序返回答案。
 *   示例 1：输入 nums = [2,7,11,15], target = 9，输出 [0,1]。因为 nums[0] + nums[1] == 9，返回 [0, 1]。
 *   示例 2：输入 nums = [3,2,4], target = 6，输出 [1,2]。
 *   示例 3：输入 nums = [3,3], target = 6，输出 [0,1]。
 *   提示：2 <= nums.length <= 10^4，-10^9 <= nums[i] <= 10^9，-10^9 <= target <= 10^9。只会存在一个有效答案。
 *   进阶：你可以想出一个时间复杂度小于 O(n^2) 的算法吗？
 * 思路：
 *   1. 初始化一个哈希表 map，用于存储“数值 -> 下标”的映射。
 *   2. 从左到右遍历数组，对于当前元素 nums[i]：
 *      a) 计算 complement = target - nums[i]。
 *      b) 如果 complement 已在 map 中，说明之前某个元素与当前元素之和为 target，直接返回 [map.get(complement), i]。
 *      c) 否则将 nums[i] 及其下标 i 存入 map。
 *   3. 若遍历结束未找到，返回空数组。
 * 数据结构：哈希表（Hash Map）—— 基于哈希函数实现键值对存储，平均 O(1) 查询/插入。
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
