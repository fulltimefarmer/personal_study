/**
 * 考点：数组、二分查找、分治、矩阵
 * 题目：Search a 2D Matrix II（搜索二维矩阵 II）
 * 题目描述：搜索每行每列都升序的二维矩阵中的目标值。
 * 示例：matrix=[[1,4,7],[2,5,8],[3,6,9]],target=5 输出 true
 * 思路：从右上角开始，matrix[row][col]>target 左移，<target 下移，每次排除一行或一列。
 * 时间复杂度：O(m + n)
 * 空间复杂度：O(1)
 */
function searchMatrix(matrix: number[][], target: number): boolean {
    const m = matrix.length;
    const n = matrix[0].length;
    let row = 0;
    let col = n - 1;

    while (row < m && col >= 0) {
        if (matrix[row][col] === target) {
            return true;
        } else if (matrix[row][col] > target) {
            col--;
        } else {
            row++;
        }
    }

    return false;
}
export { searchMatrix };
