/**
 * 考点：Stack, Array, Dynamic Programming, Matrix, Monotonic Stack
 * 题目：Maximal Rectangle（最大矩形）
 * 题目描述：给定只含 '0' 和 '1' 的二维二进制矩阵，找出只包含 '1' 的最大矩形面积。
 * 示例：matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]] → 6
 * 思路：转化为直方图最大矩形问题（LeetCode 84）。逐行构建 heights 数组（连续 1 的高度），
 *       每行用单调栈计算最大矩形面积，更新全局最大值。
 * 时间复杂度：O(rows × cols)
 * 空间复杂度：O(cols)
 */
function maximalRectangle(matrix: string[][]): number {
    if (matrix.length === 0 || matrix[0].length === 0) return 0;

    const cols = matrix[0].length;
    const heights: number[] = new Array(cols).fill(0);
    let maxArea = 0;

    for (let i = 0; i < matrix.length; i++) {
        for (let j = 0; j < cols; j++) {
            heights[j] = matrix[i][j] === '1' ? heights[j] + 1 : 0;
        }
        maxArea = Math.max(maxArea, largestRectangleInHistogram(heights));
    }

    return maxArea;
}

function largestRectangleInHistogram(heights: number[]): number {
    const stack: number[] = [];
    let maxArea = 0;
    heights.push(0);

    for (let i = 0; i < heights.length; i++) {
        while (stack.length > 0 && heights[i] < heights[stack[stack.length - 1]]) {
            const h = heights[stack.pop()!];
            const w = stack.length === 0 ? i : i - stack[stack.length - 1] - 1;
            maxArea = Math.max(maxArea, h * w);
        }
        stack.push(i);
    }

    heights.pop();
    return maxArea;
}

export { maximalRectangle };
