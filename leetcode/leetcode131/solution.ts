/**
 * 考点：字符串、动态规划、回溯
 * 题目：Palindrome Partitioning（分割回文串）
 * 题目描述：将字符串分割成若干回文子串，返回所有可能的分割方案。
 *   示例：s = "aab" → [["a","a","b"],["aa","b"]]
 * 思路：DP 预计算回文判断矩阵 + 回溯搜索所有分割方案。
 *   回溯从位置 start 开始，如果 s[start..end] 是回文则继续递归。
 * 时间复杂度：O(n × 2^n)
 * 空间复杂度：O(n²)
 */

function partition(s: string): string[][] {
  const n = s.length;
  const isPalindrome: boolean[][] = Array.from(
    { length: n },
    () => new Array(n).fill(false)
  );

  for (let j = 0; j < n; j++) {
    for (let i = 0; i <= j; i++) {
      if (s[i] === s[j] && (j - i <= 2 || isPalindrome[i + 1][j - 1])) {
        isPalindrome[i][j] = true;
      }
    }
  }

  const result: string[][] = [];

  function backtrack(start: number, path: string[]): void {
    if (start === n) {
      result.push([...path]);
      return;
    }
    for (let end = start; end < n; end++) {
      if (isPalindrome[start][end]) {
        path.push(s.substring(start, end + 1));
        backtrack(end + 1, path);
        path.pop();
      }
    }
  }

  backtrack(0, []);
  return result;
}

export { partition };
