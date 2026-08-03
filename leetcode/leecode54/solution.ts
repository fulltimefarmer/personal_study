/**
 * 考点：Array, Matrix, Simulation
 * 题目：Spiral Matrix（螺旋矩阵）
 * 题目描述：给定 m×n 矩阵，按顺时针螺旋顺序返回所有元素。
 * 示例：matrix = [[1,2,3],[4,5,6],[7,8,9]] → [1,2,3,6,9,8,7,4,5]
 * 思路：定义 top/bottom/left/right 四个边界，按 右→下→左→上 顺序遍历，每走完一条边收缩边界。
 *       注意在反向遍历前需检查边界条件，防止重复。
 * 时间复杂度：O(m × n)
 * 空间复杂度：O(1)
 */
function spiralOrder(matrix: number[][]): number[] {
    if (matrix.length === 0) return [];

    const result: number[] = [];
    let top = 0;
    let bottom = matrix.length - 1;
    let left = 0;
    let right = matrix[0].length - 1;

    while (top <= bottom && left <= right) {
        for (let col = left; col <= right; col++) {
            result.push(matrix[top][col]);
        }
        top++;

        for (let row = top; row <= bottom; row++) {
            result.push(matrix[row][right]);
        }
        right--;

        if (top <= bottom) {
            for (let col = right; col >= left; col--) {
                result.push(matrix[bottom][col]);
            }
            bottom--;
        }

        if (left <= right) {
            for (let row = bottom; row >= top; row--) {
                result.push(matrix[row][left]);
            }
            left++;
        }
    }

    return result;
}

export { spiralOrder };
