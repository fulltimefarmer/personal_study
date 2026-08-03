/**
 * 考点：字符串、动态规划
 * 题目：Distinct Subsequences（不同的子序列）
 * 题目描述：计算 s 的子序列中等于 t 的个数。
 *   示例：s = "rabbbit", t = "rabbit" → 3
 * 思路：动态规划。dp[i][j] 表示 s[0..i-1] 的子序列中等于 t[0..j-1] 的个数。
 *   状态转移：
 *     - s[i-1] === t[j-1]: dp[i][j] = dp[i-1][j-1] + dp[i-1][j]（匹配 or 跳过）
 *     - s[i-1] !== t[j-1]: dp[i][j] = dp[i-1][j]（跳过）
 *   初始化：dp[i][0] = 1, dp[0][j] = 0 (j > 0)
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(n)，使用一维滚动数组
 */

function numDistinct(s: string, t: string): number {
  const m = s.length;
  const n = t.length;
  const dp: number[] = new Array(n + 1).fill(0);
  dp[0] = 1;

  for (let i = 1; i <= m; i++) {
    for (let j = n; j >= 1; j--) {
      if (s[i - 1] === t[j - 1]) {
        dp[j] = dp[j - 1] + dp[j];
      }
    }
  }

  return dp[n];
}

export { numDistinct };
