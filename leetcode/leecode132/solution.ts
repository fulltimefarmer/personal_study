/**
 * 考点：String, Dynamic Programming
 * 题目：Palindrome Partitioning II（分割回文串II）
 * 题目描述：将字符串分割成全回文子串，求最少分割次数。
 * 示例 1：s = "aab"，输出 1（["aa","b"]）
 * 示例 2：s = "a"，输出 0
 * 示例 3：s = "ab"，输出 1
 * 思路：DP 预处理回文表，再 DP 求最少分割次数。
 * dp[i] = min(dp[i], j===0 ? 0 : dp[j-1]+1)，当 s[j..i] 是回文。
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(n^2)
 */
function minCut(s: string): number {
    const n = s.length;
    const isPal: boolean[][] = Array.from({ length: n }, () => new Array(n).fill(false));

    for (let i = n - 1; i >= 0; i--) {
        for (let j = i; j < n; j++) {
            if (s[i] === s[j] && (j - i <= 1 || isPal[i + 1][j - 1])) {
                isPal[i][j] = true;
            }
        }
    }

    const dp: number[] = new Array(n).fill(0);

    for (let i = 0; i < n; i++) {
        if (isPal[0][i]) {
            dp[i] = 0;
            continue;
        }
        dp[i] = i;
        for (let j = 1; j <= i; j++) {
            if (isPal[j][i]) {
                dp[i] = Math.min(dp[i], dp[j - 1] + 1);
            }
        }
    }

    return dp[n - 1];
}

export { minCut };
