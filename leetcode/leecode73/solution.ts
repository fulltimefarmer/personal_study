/**
 * 考点：Array, Hash Table, Matrix
 * 题目：Set Matrix Zeroes（矩阵置零）
 * 题目描述：给定 m×n 矩阵，若元素为 0，将其所在行和列全部置零。要求原地算法，O(1) 额外空间。
 * 示例：matrix = [[1,1,1],[1,0,1],[1,1,1]] → [[1,0,1],[0,0,0],[1,0,1]]
 * 思路：利用第一行和第一列作为标记。先记录第一行/第一列是否需要置零，
 *       再用它们标记需要置零的行列，最后根据标记置零。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(1)
 */
function setZeroes(matrix: number[][]): void {
    const m = matrix.length;
    const n = matrix[0].length;

    let firstRowZero = false;
    let firstColZero = false;

    for (let j = 0; j < n; j++) {
        if (matrix[0][j] === 0) {
            firstRowZero = true;
            break;
        }
    }

    for (let i = 0; i < m; i++) {
        if (matrix[i][0] === 0) {
            firstColZero = true;
            break;
        }
    }

    for (let i = 1; i < m; i++) {
        for (let j = 1; j < n; j++) {
            if (matrix[i][j] === 0) {
                matrix[i][0] = 0;
                matrix[0][j] = 0;
            }
        }
    }

    for (let i = 1; i < m; i++) {
        for (let j = 1; j < n; j++) {
            if (matrix[i][0] === 0 || matrix[0][j] === 0) {
                matrix[i][j] = 0;
            }
        }
    }

    if (firstRowZero) {
        for (let j = 0; j < n; j++) {
            matrix[0][j] = 0;
        }
    }

    if (firstColZero) {
        for (let i = 0; i < m; i++) {
            matrix[i][0] = 0;
        }
    }
}

export { setZeroes };
