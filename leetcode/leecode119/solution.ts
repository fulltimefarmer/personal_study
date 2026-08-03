/**
 * 考点：Array, Dynamic Programming
 * 题目：Pascal's Triangle II（杨辉三角II）
 * 题目描述：返回杨辉三角的第 rowIndex 行（0 索引）。
 * 示例 1：rowIndex = 3，输出 [1,3,3,1]
 * 示例 2：rowIndex = 0，输出 [1]
 * 示例 3：rowIndex = 1，输出 [1,1]
 * 思路：滚动数组，从后向前更新，空间 O(k)。
 * 时间复杂度：O(rowIndex^2)
 * 空间复杂度：O(rowIndex)
 */
function getRow(rowIndex: number): number[] {
    const row: number[] = new Array(rowIndex + 1).fill(0);
    row[0] = 1;

    for (let i = 1; i <= rowIndex; i++) {
        for (let j = i; j >= 1; j--) {
            row[j] = row[j] + row[j - 1];
        }
    }

    return row;
}

export { getRow };
