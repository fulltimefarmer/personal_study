/**
 * 考点：Array, Two Pointers, Greedy
 * 题目：Container With Most Water（盛最多水的容器）
 * 题目描述：给定数组 height，找出两条线使其与 x 轴构成的容器可以容纳最多的水，返回最大水量。
 * 示例：height = [1,8,6,2,5,4,8,3,7] => 49
 * 思路：双指针从两端向中间收缩，每次移动较短的边，更新最大面积
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxArea(height: number[]): number {
    let left = 0;
    let right = height.length - 1;
    let maxArea = 0;

    while (left < right) {
        const h = Math.min(height[left], height[right]);
        const area = h * (right - left);
        maxArea = Math.max(maxArea, area);

        if (height[left] < height[right]) {
            left++;
        } else {
            right--;
        }
    }

    return maxArea;
}
export { maxArea };
