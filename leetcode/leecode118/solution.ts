/**
 * 考点：Array, Dynamic Programming
 * 题目：Pascal's Triangle（杨辉三角）
 * 题目描述：生成杨辉三角的前 numRows 行。每个数是它左上方和右上方的数的和。
 * 示例 1：numRows = 5，输出 [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]
 * 示例 2：numRows = 1，输出 [[1]]
 * 思路：逐行构建，首尾元素为 1，中间元素为上一行相邻两元素之和。
 * 时间复杂度：O(numRows^2)
 * 空间复杂度：O(1)（不计返回值）
 */
function generate(numRows: number): number[][] {
    const result: number[][] = [];

    for (let i = 0; i < numRows; i++) {
        const row: number[] = new Array(i + 1).fill(1);
        for (let j = 1; j < i; j++) {
            row[j] = result[i - 1][j - 1] + result[i - 1][j];
        }
        result.push(row);
    }

    return result;
}

export { generate };
