/**
 * 考点：数组、动态规划
 * 题目：Triangle（三角形最小路径和）
 * 题目描述：从三角形顶部到底部的最小路径和，每一步只能移动到下一行同下标或下标+1的位置。
 *   示例：triangle = [[2],[3,4],[6,5,7],[4,1,8,3]] → 11（2→3→5→1）
 * 思路：自底向上 DP。dp[j] = triangle[i][j] + min(dp[j], dp[j+1])。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n)
 */

function minimumTotal(triangle: number[][]): number {
  const n = triangle.length;
  const dp: number[] = [...triangle[n - 1]];

  for (let i = n - 2; i >= 0; i--) {
    for (let j = 0; j <= i; j++) {
      dp[j] = triangle[i][j] + Math.min(dp[j], dp[j + 1]);
    }
  }

  return dp[0];
}

export { minimumTotal };
