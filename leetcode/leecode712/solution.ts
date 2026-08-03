/**
 * 考点：字符串, 动态规划
 * 题目：Minimum ASCII Delete Sum for Two Strings（两个字符串的最小ASCII删除和）
 * 题目描述：给定 s1 和 s2，求使两字符串相等所需删除字符的 ASCII 值的最小和。
 * 示例：
 *   输入: "sea", "eat" → 输出: 231 (s1删's'115 + s2删't'116 = 231)
 * 思路：DP。dp[i][j] 使 s1[0..i] 和 s2[0..j] 相等的最小删除和。相等时 dp[i][j]=dp[i-1][j-1]；否则 min(删s1[i], 删s2[j])。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function minimumDeleteSum(s1: string, s2: string): number {
    const m = s1.length;
    const n = s2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        dp[i][0] = dp[i - 1][0] + s1.charCodeAt(i - 1);
    }
    for (let j = 1; j <= n; j++) {
        dp[0][j] = dp[0][j - 1] + s2.charCodeAt(j - 1);
    }

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (s1[i - 1] === s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = Math.min(
                    dp[i - 1][j] + s1.charCodeAt(i - 1),
                    dp[i][j - 1] + s2.charCodeAt(j - 1)
                );
            }
        }
    }

    return dp[m][n];
}

export { minimumDeleteSum };
