/**
 * 考点：字符串、动态规划
 * 题目：Palindrome Partitioning II（分割回文串 II）
 * 题目描述：求将字符串分割为若干回文子串的最少分割次数。
 *   示例：s = "aab" → 1（分割成 ["aa","b"]）
 * 思路：中心扩展法同时计算回文并更新 DP。
 *   dp[i] 表示 s[0..i] 的最少分割次数。
 *   以每个位置为中心扩展回文，当扩展到 [left, right] 时：
 *     - left === 0: dp[right] = 0
 *     - 否则: dp[right] = min(dp[right], dp[left-1] + 1)
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n)
 */

function minCut(s: string): number {
  const n = s.length;
  const dp: number[] = new Array(n).fill(0).map((_, i) => i);

  for (let center = 0; center < n; center++) {
    expand(center, center);
    expand(center, center + 1);
  }

  function expand(left: number, right: number): void {
    while (left >= 0 && right < n && s[left] === s[right]) {
      if (left === 0) {
        dp[right] = 0;
      } else {
        dp[right] = Math.min(dp[right], dp[left - 1] + 1);
      }
      left--;
      right++;
    }
  }

  return dp[n - 1];
}

export { minCut };
