/**
 * 考点：字符串, 动态规划
 * 题目：Delete Operation for Two Strings（两个字符串的删除操作）
 * 题目描述：给定 word1 和 word2，每步可删除任意一个字符串的一个字符。求使两个字符串相同的最少步数。
 * 示例：
 *   输入: "sea", "eat" → 输出: 2
 * 思路：最小删除步数 = len1 + len2 - 2*LCS。先求最长公共子序列长度，再计算答案。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function minDistance(word1: string, word2: string): number {
    const m = word1.length;
    const n = word2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (word1[i - 1] === word2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    const lcs = dp[m][n];
    return m + n - 2 * lcs;
}

export { minDistance };
