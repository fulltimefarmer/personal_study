/**
 * 考点：String, Dynamic Programming
 * 题目：Edit Distance（编辑距离）
 * 题目描述：给定两个单词 word1 和 word2，返回将 word1 转换为 word2 的最少操作数（插入、删除、替换）。
 * 示例：word1 = "horse", word2 = "ros" → 3
 * 示例：word1 = "intention", word2 = "execution" → 5
 * 思路：动态规划（Levenshtein 距离）。
 *       dp[i][j]: word1[0..i) 转 word2[0..j) 的最少操作数。
 *       若 word1[i-1]==word2[j-1]，dp[i][j]=dp[i-1][j-1]；
 *       否则 dp[i][j]=1+min(dp[i-1][j](删), dp[i][j-1](插), dp[i-1][j-1](换))。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)
 */
function minDistance(word1: string, word2: string): number {
    const m = word1.length;
    const n = word2.length;

    const dp: number[] = new Array(n + 1);
    for (let j = 0; j <= n; j++) {
        dp[j] = j;
    }

    for (let i = 1; i <= m; i++) {
        let prev = dp[0];
        dp[0] = i;
        for (let j = 1; j <= n; j++) {
            const temp = dp[j];
            if (word1[i - 1] === word2[j - 1]) {
                dp[j] = prev;
            } else {
                dp[j] = 1 + Math.min(prev, dp[j], dp[j - 1]);
            }
            prev = temp;
        }
    }

    return dp[n];
}

export { minDistance };
