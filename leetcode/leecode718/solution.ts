/**
 * 考点：数组, 二分搜索, 动态规划, 滑动窗口, 滚动哈希
 * 题目：Maximum Length of Repeated Subarray（最长重复子数组）
 * 题目描述：给定两个整数数组 nums1 和 nums2，返回它们的最长公共子数组的长度（子数组要连续）。
 * 示例：
 *   输入: nums1=[1,2,3,2,1], nums2=[3,2,1,4,7] → 输出: 3 ([3,2,1])
 * 思路：DP。dp[i][j] 表示以 nums1[i-1] 和 nums2[j-1] 结尾的最长公共子数组长度。相等则 dp[i][j]=dp[i-1][j-1]+1，否则为 0。取最大值。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function findLength(nums1: number[], nums2: number[]): number {
    const m = nums1.length;
    const n = nums2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    let maxLen = 0;

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (nums1[i - 1] === nums2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
                maxLen = Math.max(maxLen, dp[i][j]);
            }
        }
    }

    return maxLen;
}

export { findLength };
