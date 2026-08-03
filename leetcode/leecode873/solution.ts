/**
 * 考点：数组, 哈希表, 动态规划
 * 题目：Length of Longest Fibonacci Subsequence（最长的斐波那契子序列的长度）
 * 题目描述：给定严格递增数组 arr，找出最长的斐波那契式子序列（X_i + X_{i+1} = X_{i+2}）的长度，不存在返回 0。
 * 示例：
 *   输入: [1,2,3,4,5,6,7,8] → 输出: 5 ([1,2,3,5,8])
 * 思路：DP+哈希表。dp[i][j] 表示以 arr[i],arr[j] 结尾的斐波那契子序列长度。target=arr[j]-arr[i]，若存在且索引k<i，则 dp[i][j]=dp[k][i]+1。记录最大值。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n²)
 */
function lenLongestFibSubseq(arr: number[]): number {
    const n = arr.length;
    const indexMap = new Map<number, number>();
    for (let i = 0; i < n; i++) {
        indexMap.set(arr[i], i);
    }

    const dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(2));
    let maxLen = 0;

    for (let j = 1; j < n; j++) {
        for (let i = 0; i < j; i++) {
            const target = arr[j] - arr[i];
            if (target < arr[i] && indexMap.has(target)) {
                const k = indexMap.get(target)!;
                dp[i][j] = dp[k][i] + 1;
                maxLen = Math.max(maxLen, dp[i][j]);
            }
        }
    }

    return maxLen >= 3 ? maxLen : 0;
}

export { lenLongestFibSubseq };
