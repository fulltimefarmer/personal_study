/**
 * 考点：String, Dynamic Programming
 * 题目：Distinct Subsequences（不同的子序列）
 * 题目描述：给定字符串 s 和 t，计算 s 的子序列中 t 出现的个数，对 10^9+7 取模。
 * 示例 1：s = "rabbbit", t = "rabbit"，输出 3
 * 示例 2：s = "babgbag", t = "bag"，输出 5
 * 思路：DP，dp[i][j] 表示 s[0..i-1] 的子序列中 t[0..j-1] 出现的次数。
 * 若 s[i-1]==t[j-1]，dp[i][j]=dp[i-1][j-1]+dp[i-1][j]；否则 dp[i][j]=dp[i-1][j]。
 * 初始化 dp[i][0]=1。
 * 时间复杂度：O(m*n)
 * 空间复杂度：O(n)（滚动数组优化）
 */
function numDistinct(s: string, t: string): number {
    const MOD = 1e9 + 7;
    const m = s.length;
    const n = t.length;
    const dp: number[] = new Array(n + 1).fill(0);
    dp[0] = 1;

    for (let i = 1; i <= m; i++) {
        for (let j = n; j >= 1; j--) {
            if (s[i - 1] === t[j - 1]) {
                dp[j] = (dp[j] + dp[j - 1]) % MOD;
            }
        }
    }

    return dp[n];
}

export { numDistinct };
