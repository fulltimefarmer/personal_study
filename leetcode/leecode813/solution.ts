/**
 * 考点：数组, 数学, 动态规划, 前缀和
 * 题目：Largest Sum of Averages（最大平均值和的分组）
 * 题目描述：将数组 nums 分成最多 k 个非空连续子数组，求各子数组平均值之和的最大值。
 * 示例：
 *   输入: nums=[9,1,2,3,9], k=3 → 输出: 20
 * 思路：DP+前缀和。dp[i][m] 表示前 i 个元素分 m 组的最大分数。dp[i][m] = max(dp[j][m-1] + (prefixSum[i]-prefixSum[j])/(i-j))。
 * 时间复杂度：O(n² * k)
 * 空间复杂度：O(n * k)
 */
function largestSumOfAverages(nums: number[], k: number): number {
    const n = nums.length;
    const prefixSum: number[] = new Array(n + 1).fill(0);
    for (let i = 0; i < n; i++) {
        prefixSum[i + 1] = prefixSum[i] + nums[i];
    }

    const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(k + 1).fill(0));

    for (let i = 1; i <= n; i++) {
        dp[i][1] = prefixSum[i] / i;
    }

    for (let m = 2; m <= k; m++) {
        for (let i = m; i <= n; i++) {
            for (let j = m - 1; j < i; j++) {
                const avg = (prefixSum[i] - prefixSum[j]) / (i - j);
                dp[i][m] = Math.max(dp[i][m], dp[j][m - 1] + avg);
            }
        }
    }

    return dp[n][k];
}

export { largestSumOfAverages };
