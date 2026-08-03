/**
 * 考点：位运算、动态规划
 * 题目：Counting Bits（比特位计数）
 * 题目描述：对 0 到 n 的每个数，计算二进制中 1 的个数
 * 思路：DP 递推。dp[i] = dp[i >> 1] + (i & 1)
 *       即 i 的 popcount = i/2 的 popcount + i 的最低位。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)（不含结果数组）
 */
function countBits(n: number): number[] {
    const dp = new Array(n + 1).fill(0);

    for (let i = 1; i <= n; i++) {
        dp[i] = dp[i >> 1] + (i & 1);
    }

    return dp;
}

export { countBits };
