/**
 * 考点：Trie, Memoization, Hash Table, String, DP
 * 题目：Word Break（单词拆分）
 * 题目描述：判断字符串 s 是否可以由字典 wordDict 中的单词拼接而成，单词可重复使用。
 * 示例 1：s="leetcode", wordDict=["leet","code"]，输出 true
 * 示例 2：s="applepenapple", wordDict=["apple","pen"]，输出 true
 * 示例 3：s="catsandog", wordDict=["cats","dog","sand","and","cat"]，输出 false
 * 思路：DP，dp[i] 表示 s[0..i-1] 是否可拆分。dp[i]=true 如果 dp[j] 且 s[j..i-1] 在字典中。
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(n+m)
 */
function wordBreak(s: string, wordDict: string[]): boolean {
    const wordSet = new Set(wordDict);
    const n = s.length;
    const dp: boolean[] = new Array(n + 1).fill(false);
    dp[0] = true;

    for (let i = 1; i <= n; i++) {
        for (let j = 0; j < i; j++) {
            if (dp[j] && wordSet.has(s.substring(j, i))) {
                dp[i] = true;
                break;
            }
        }
    }

    return dp[n];
}

export { wordBreak };
