/**
 * 考点：Array, Two Pointers, Greedy
 * 题目：Container With Most Water（盛最多水的容器）
 * 题目描述：数组中每条垂线高度为height[i]，找两条线使容器面积最大。面积 = min(h1,h2) * 宽度。
 * 思路：双指针从两端开始，每次移动较短边，尝试用更大的高度弥补宽度减少。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxArea(height: number[]): number {
    let left = 0;
    let right = height.length - 1;
    let maxArea = 0;

    while (left < right) {
        const area = Math.min(height[left], height[right]) * (right - left);
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
