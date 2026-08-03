/**
 * 考点：字符串, 动态规划
 * 题目：Longest Palindromic Subsequence（最长回文子序列）
 * 题目描述：给定字符串 s，求最长回文子序列的长度。子序列可以不连续。
 * 示例：
 *   输入: "bbbab" → 输出: 4 ("bbbb")
 *   输入: "cbbd" → 输出: 2 ("bb")
 * 思路：区间 DP。dp[i][j] 表示 s[i..j] 的最长回文子序列长度。若 s[i]==s[j]，dp[i][j]=dp[i+1][j-1]+2；否则 dp[i][j]=max(dp[i+1][j], dp[i][j-1])。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n²)
 */
function longestPalindromeSubseq(s: string): number {
    const n = s.length;
    const dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));

    for (let i = n - 1; i >= 0; i--) {
        dp[i][i] = 1;
        for (let j = i + 1; j < n; j++) {
            if (s[i] === s[j]) {
                dp[i][j] = dp[i + 1][j - 1] + 2;
            } else {
                dp[i][j] = Math.max(dp[i + 1][j], dp[i][j - 1]);
            }
        }
    }

    return dp[0][n - 1];
}

export { longestPalindromeSubseq };
