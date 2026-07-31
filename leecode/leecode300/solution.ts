/**
 * 考点：Dynamic Programming、Binary Search
 * 题目：Longest Increasing Subsequence（最长递增子序列）
 * 题目描述：
 *   给你一个整数数组 nums，找到其中最长严格递增子序列的长度。
 *   子序列是由数组派生而来的序列，删除（或不删除）数组中的元素而不改变其余元素的顺序。例如，[3,6,2,7] 是数组 [0,3,1,6,2,2,7] 的子序列。
 *   示例 1：
 *   输入：nums = [10,9,2,5,3,7,101,18]
 *   输出：4
 *   解释：最长递增子序列是 [2,3,7,101]，因此长度为 4。
 *   示例 2：
 *   输入：nums = [0,1,0,3,2,3]
 *   输出：4
 *   示例 3：
 *   输入：nums = [7,7,7,7,7,7,7]
 *   输出：1
 *   提示：
 *   - 1 <= nums.length <= 2500
 *   - -10^4 <= nums[i] <= 10^4
 *   进阶：你能将算法的时间复杂度降到 O(n log(n)) 吗？
 * 思路：
 *   1. 维护一个数组 tails，其中 tails[i] 表示长度为 i+1 的递增子序列的“最小末尾元素”。
 *   2.  tails 数组一定是严格递增的，因此可以用二分查找快速定位当前数字应该替换的位置。
 *   3. 遍历每个数字 num：在 tails 中找到第一个大于等于 num 的位置 left。
 *      - 若 num 比 tails 中所有元素都大（left == tails.length），说明可以延长当前最长递增子序列，将 num 追加到 tails 末尾。
 *      - 否则用 num 替换 tails[left]，让同长度递增子序列的结尾更小，更有利于后续数字接在后面。
 *   4. 遍历完成后，tails 的长度即为最长递增子序列的长度。
 * 算法：patience sorting / 贪心 + 二分 —— 使每个长度的结尾尽可能小，以容纳更多后续数字。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(n)
 */
function lengthOfLIS(nums: number[]): number {
    const tails: number[] = [];

    for (const num of nums) {
        let left = 0;
        let right = tails.length;
        while (left < right) {
            const mid = Math.floor((left + right) / 2);
            if (tails[mid] < num) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        if (left === tails.length) {
            tails.push(num);
        } else {
            tails[left] = num;
        }
    }

    return tails.length;
}
