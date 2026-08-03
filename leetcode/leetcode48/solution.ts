/**
 * 考点：Array, Math, Matrix
 * 题目：Rotate Image（旋转图像）
 * 题目描述：n×n矩阵原地顺时针旋转90°。如 [[1,2,3],[4,5,6],[7,8,9]] → [[7,4,1],[8,5,2],[9,6,3]]
 * 思路：先转置（对角线交换），再水平翻转（每行反转）。两步都是原地操作。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(1)
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
