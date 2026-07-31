/**
 * 考点：Array, Hash Table, Boyer-Moore Voting Algorithm
 * 题目：Majority Element
 * 题目描述：
 * 给定一个大小为 n 的数组 nums，返回其中的多数元素。
 *
 * 多数元素是指在数组中出现次数大于 ⌊ n/2 ⌋ 的元素。
 * 你可以假设数组是非空的，并且给定的数组总是存在多数元素。
 *
 * 示例 1：
 * 输入：nums = [3,2,3]
 * 输出：3
 *
 * 示例 2：
 * 输入：nums = [2,2,1,1,1,2,2]
 * 输出：2
 *
 * 提示：
 * - n == nums.length
 * - 1 <= n <= 5 * 10^4
 * - -10^9 <= nums[i] <= 10^9
 *
 * 进阶：尝试设计时间复杂度为 O(n)、空间复杂度为 O(1) 的算法解决此问题。
 *
 * 思路：
 * 1. 使用 Boyer-Moore 摩尔投票算法，初始化候选人 candidate 为任意值，计数 count 为 0。
 * 2. 遍历数组中的每个元素 num：
 *    - 若 count 为 0，说明当前没有候选人，将 candidate 设为 num，count 设为 1。
 *    - 若 num 等于 candidate，则 count 加 1；否则 count 减 1。
 * 3. 由于多数元素出现次数超过 n/2，不同元素之间会相互抵消，最终 candidate 一定为多数元素。
 * 4. 返回 candidate。
 * 数据结构/算法：摩尔投票算法（Boyer-Moore Voting），不需要额外哈希表。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function majorityElement(nums: number[]): number {
    let candidate = 0;
    let count = 0;
    for (const num of nums) {
        if (count === 0) {
            candidate = num;
        }
        count += num === candidate ? 1 : -1;
    }
    return candidate;
}
