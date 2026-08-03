/**
 * 考点：Stack, Array, Monotonic Stack
 * 题目：Largest Rectangle in Histogram（柱状图中最大的矩形）
 * 题目描述：给定柱状图的高度数组 heights，求能勾勒出的最大矩形面积。
 * 示例：heights = [2,1,5,6,2,3] → 10
 * 思路：单调递增栈。对每个柱子找左右第一个比它矮的柱子作为边界，计算以它为高的矩形面积。
 *       末尾加哨兵 0 确保所有元素被处理。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function largestRectangleArea(heights: number[]): number {
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

export { largestRectangleArea };
