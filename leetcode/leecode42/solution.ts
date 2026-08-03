/**
 * 考点：Stack, Array, Two Pointers, Dynamic Programming, Monotonic Stack
 * 题目：Trapping Rain Water（接雨水）
 * 题目描述：给定非负整数数组表示柱子高度，计算下雨后能接多少雨水。
 * 示例：height = [0,1,0,2,1,0,1,3,2,1,2,1] => 6
 * 思路：双指针法，维护左右最大高度，每个位置的水量由较短的挡板决定
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function trap(height: number[]): number {
    if (height.length === 0) return 0;

    let left = 0;
    let right = height.length - 1;
    let leftMax = 0;
    let rightMax = 0;
    let water = 0;

    while (left < right) {
        if (height[left] < height[right]) {
            if (height[left] >= leftMax) {
                leftMax = height[left];
            } else {
                water += leftMax - height[left];
            }
            left++;
        } else {
            if (height[right] >= rightMax) {
                rightMax = height[right];
            } else {
                water += rightMax - height[right];
            }
            right--;
        }
    }

    return water;
}
export { trap };
