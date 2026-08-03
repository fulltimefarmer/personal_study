/**
 * 考点：Array, Math, Matrix
 * 题目：Rotate Image（旋转图像）
 * 题目描述：原地将 n×n 矩阵顺时针旋转 90 度。
 * 示例：matrix = [[1,2,3],[4,5,6],[7,8,9]] => [[7,4,1],[8,5,2],[9,6,3]]
 * 思路：先沿主对角线转置，再水平翻转每行
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(1)
 */

/**
 Do not return anything, modify matrix in-place instead.
 */
function rotate(matrix: number[][]): void {
    const n = matrix.length;

    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];
        }
    }

    for (let i = 0; i < n; i++) {
        for (let j = 0; j < Math.floor(n / 2); j++) {
            [matrix[i][j], matrix[i][n - 1 - j]] = [matrix[i][n - 1 - j], matrix[i][j]];
        }
    }
}
export { rotate };
