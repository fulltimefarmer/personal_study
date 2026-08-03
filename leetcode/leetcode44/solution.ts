/**
 * 考点：Greedy, Recursion, String, Dynamic Programming
 * 题目：Wildcard Matching（通配符匹配）
 * 题目描述：实现支持 '?'（匹配单字符）和 '*'（匹配任意串）的通配符匹配。如 s="aa", p="*" → true
 * 思路：DP，dp[i][j]表示s[0..i-1]和p[0..j-1]是否匹配。遇'*'时dp[i][j]=dp[i][j-1]||dp[i-1][j]。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(m × n)
 */
function isWildcardMatch(s: string, p: string): boolean {
    const m = s.length;
    const n = p.length;
    const dp: boolean[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(false));

    dp[0][0] = true;
    for (let j = 1; j <= n; j++) {
        if (p[j - 1] === '*') {
            dp[0][j] = dp[0][j - 1];
        }
    }

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (p[j - 1] !== '*') {
                dp[i][j] = dp[i - 1][j - 1] && (s[i - 1] === p[j - 1] || p[j - 1] === '?');
            } else {
                dp[i][j] = dp[i][j - 1] || dp[i - 1][j];
            }
        }
    }

    return dp[m][n];
}

export { isWildcardMatch };
