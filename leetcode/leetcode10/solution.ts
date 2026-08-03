/**
 * 考点：String, Dynamic Programming, Recursion
 * 题目：Regular Expression Matching（正则表达式匹配）
 * 题目描述：实现支持 '.' 和 '*' 的正则匹配。'.' 匹配任意单字符，'*' 匹配前一个字符0次或多次。
 * 思路：DP，dp[i][j] 表示 s[0..i-1] 和 p[0..j-1] 是否匹配。处理 '*' 时分匹配0次和匹配≥1次两种情况。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(m × n)
 */
function isMatch(s: string, p: string): boolean {
    const m = s.length;
    const n = p.length;
    const dp: boolean[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(false));

    dp[0][0] = true;
    for (let j = 2; j <= n; j++) {
        if (p[j - 1] === '*') {
            dp[0][j] = dp[0][j - 2];
        }
    }

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (p[j - 1] !== '*') {
                dp[i][j] = dp[i - 1][j - 1] && (s[i - 1] === p[j - 1] || p[j - 1] === '.');
            } else {
                dp[i][j] = dp[i][j - 2] ||
                    (dp[i - 1][j] && (s[i - 1] === p[j - 2] || p[j - 2] === '.'));
            }
        }
    }

    return dp[m][n];
}

export { isMatch };
