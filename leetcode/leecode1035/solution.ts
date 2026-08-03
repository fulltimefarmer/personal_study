/**
 * 考点：数组, 动态规划
 * 题目：Uncrossed Lines（不相交的线）
 * 题目描述：在 nums1 和 nums2 中连接相等的数字，连线不能相交。求最大连线数。
 * 示例：
 *   输入: nums1=[1,4,2], nums2=[1,2,4] → 输出: 2
 *   输入: nums1=[2,5,1,2,5], nums2=[10,5,2,1,5,2] → 输出: 3
 * 思路：本质是求 LCS（最长公共子序列）。dp[i][j] 表示 nums1[0..i-1] 和 nums2[0..j-1] 的 LCS 长度。nums1[i-1]==nums2[j-1] 则 dp[i][j]=dp[i-1][j-1]+1，否则 max(dp[i-1][j], dp[i][j-1])。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function maxUncrossedLines(nums1: number[], nums2: number[]): number {
    const m = nums1.length;
    const n = nums2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (nums1[i - 1] === nums2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    return dp[m][n];
}

export { maxUncrossedLines };
