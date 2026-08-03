/**
 * 考点：Stack, Array, Two Pointers, Dynamic Programming
 * 题目：Trapping Rain Water（接雨水）
 * 题目描述：计算柱状图能接多少雨水。如 [0,1,0,2,1,0,1,3,2,1,2,1] → 6
 * 思路：双指针从两端收缩，维护leftMax和rightMax。矮边决定水量，累加差值。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function trap(height: number[]): number {
    let left = 0;
    let right = height.length - 1;
    let leftMax = 0;
    let rightMax = 0;
    let result = 0;

    while (left < right) {
        if (height[left] < height[right]) {
            if (height[left] >= leftMax) {
                leftMax = height[left];
            } else {
                result += leftMax - height[left];
            }
            left++;
        } else {
            if (height[right] >= rightMax) {
                rightMax = height[right];
            } else {
                result += rightMax - height[right];
            }
            right--;
        }
    }

    return result;
}

export { trap };
