/**
 * 考点：字符串, 动态规划
 * 题目：Longest Common Subsequence（最长公共子序列）
 * 题目描述：给定两个字符串 text1 和 text2，返回它们的最长公共子序列的长度。子序列可以不连续但保持顺序。
 * 示例：
 *   输入: text1="abcde", text2="ace" → 输出: 3 ("ace")
 *   输入: text1="abc", text2="def" → 输出: 0
 * 思路：经典 LCS DP。dp[i][j] 表示 text1[0..i-1] 和 text2[0..j-1] 的 LCS 长度。相等则 dp[i][j]=dp[i-1][j-1]+1；否则 dp[i][j]=max(dp[i-1][j], dp[i][j-1])。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function longestCommonSubsequence(text1: string, text2: string): number {
    const m = text1.length;
    const n = text2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (text1[i - 1] === text2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    return dp[m][n];
}

export { longestCommonSubsequence };
