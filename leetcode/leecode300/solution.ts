/**
 * 考点：数组、二分查找、动态规划
 * 题目：Longest Increasing Subsequence（最长递增子序列）
 * 题目描述：给定整数数组，求最长严格递增子序列的长度
 * 思路：贪心 + 二分。维护 tails 数组，tails[k] 为长度 k+1 的 LIS 的最小结尾。
 *       遍历 nums，二分查找插入位置，若比所有都大则追加，否则替换。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(n)
 */
function lengthOfLIS(nums: number[]): number {
    const tails: number[] = [];

    for (const num of nums) {
        let left = 0, right = tails.length;
        while (left < right) {
            const mid = (left + right) >> 1;
            if (tails[mid] < num) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        tails[left] = num;
    }

    return tails.length;
}

export { lengthOfLIS };
