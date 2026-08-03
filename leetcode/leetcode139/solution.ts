/**
 * 考点：字典树、记忆化搜索、数组、哈希表、字符串、动态规划
 * 题目：Word Break（单词拆分）
 * 题目描述：判断字符串 s 是否可以被字典中的单词拼接而成。单词可重复使用。
 *   示例：s = "leetcode", wordDict = ["leet","code"] → true
 * 思路：动态规划。dp[i] 表示 s[0..i-1] 是否可被拼接。
 *   dp[j] && wordDict 包含 s[j..i-1] → dp[i] = true
 * 时间复杂度：O(n²)，n = s.length
 * 空间复杂度：O(n + m)
 */

function wordBreak(s: string, wordDict: string[]): boolean {
  const wordSet = new Set(wordDict);
  const n = s.length;
  const dp: boolean[] = new Array(n + 1).fill(false);
  dp[0] = true;

  const maxLen = Math.max(...wordDict.map((w) => w.length));

  for (let i = 1; i <= n; i++) {
    for (let j = Math.max(0, i - maxLen); j < i; j++) {
      if (dp[j] && wordSet.has(s.substring(j, i))) {
        dp[i] = true;
        break;
      }
    }
  }

  return dp[n];
}

export { wordBreak };
