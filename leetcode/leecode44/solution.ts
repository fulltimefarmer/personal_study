/**
 * 考点：Greedy, Recursion, String, Dynamic Programming
 * 题目：Wildcard Matching（通配符匹配）
 * 题目描述：实现支持 '?' 和 '*' 的通配符匹配，'?' 匹配任意单字符，'*' 匹配任意字符串。
 * 示例：s = "aa", p = "*" => true
 * 思路：动态规划，dp[i][j] 表示 s[0..i-1] 和 p[0..j-1] 是否匹配
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(m * n)
 */
function isMatch(s: string, p: string): boolean {
    const m = s.length;
    const n = p.length;
    const dp: boolean[][] = Array.from({ length: m + 1 }, () =>
        Array.from({ length: n + 1 }, () => false)
    );

    dp[0][0] = true;

    for (let j = 1; j <= n; j++) {
        if (p[j - 1] === "*") {
            dp[0][j] = dp[0][j - 1];
        }
    }

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (p[j - 1] === "*") {
                dp[i][j] = dp[i - 1][j] || dp[i][j - 1];
            } else if (p[j - 1] === "?" || p[j - 1] === s[i - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            }
        }
    }

    return dp[m][n];
}
export { isMatch };
