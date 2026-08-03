/**
 * 考点：数组、动态规划
 * 题目：Pascal's Triangle II（杨辉三角 II）
 * 题目描述：返回杨辉三角的第 rowIndex 行。rowIndex 从 0 开始计数。
 *   示例：rowIndex = 3 → [1,3,3,1]
 * 思路：滚动数组 + 倒序更新。使用组合数递推公式：row[k] = row[k-1] * (n - k + 1) / k。
 * 时间复杂度：O(rowIndex)
 * 空间复杂度：O(rowIndex)
 */

function getRow(rowIndex: number): number[] {
  const row: number[] = new Array(rowIndex + 1).fill(1);

  for (let i = 1; i < rowIndex; i++) {
    for (let j = i; j > 0; j--) {
      row[j] = row[j] + row[j - 1];
    }
  }

  return row;
}

export { getRow };
