/**
 * 考点：String, Dynamic Programming
 * 题目：Interleaving String（交错字符串）
 * 题目描述：验证 s3 是否由 s1 和 s2 交错组成（保持各自字符顺序）。
 * 示例：s1="aabcc", s2="dbbca", s3="aadbbcbcac" → true
 * 示例：s1="aabcc", s2="dbbca", s3="aadbbbaccc" → false
 * 思路：动态规划。dp[i][j] 表示 s1[0..i) 和 s2[0..j) 能否交错组成 s3[0..i+j)。
 *       dp[i][j] = (s1[i-1]==s3[i+j-1] && dp[i-1][j]) || (s2[j-1]==s3[i+j-1] && dp[i][j-1])。
 *       空间优化为一维数组。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)
 */
function isInterleave(s1: string, s2: string, s3: string): boolean {
    const m = s1.length;
    const n = s2.length;

    if (m + n !== s3.length) return false;

    const dp: boolean[] = new Array(n + 1).fill(false);
    dp[0] = true;

    for (let j = 1; j <= n; j++) {
        dp[j] = dp[j - 1] && s2[j - 1] === s3[j - 1];
    }

    for (let i = 1; i <= m; i++) {
        dp[0] = dp[0] && s1[i - 1] === s3[i - 1];
        for (let j = 1; j <= n; j++) {
            dp[j] = (s1[i - 1] === s3[i + j - 1] && dp[j]) ||
                    (s2[j - 1] === s3[i + j - 1] && dp[j - 1]);
        }
    }

    return dp[n];
}

export { isInterleave };
