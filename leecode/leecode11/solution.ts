/**
 * 考点：Two Pointers
 * 题目：Container With Most Water
 * 题目描述：
 *   给定一个长度为 n 的整数数组 height。有 n 条垂线，第 i 条线的两个端点分别是 (i, 0) 和 (i, height[i])。
 *   找出其中的两条线，使得它们与 x 轴共同构成的容器可以容纳最多的水。
 *   返回容器可以储存的最大水量。
 *   说明：你不能倾斜容器。
 *   示例 1：输入 height = [1,8,6,2,5,4,8,3,7]，输出 49。解释：图中垂直线代表输入数组，由数组 [1,8,6,2,5,4,8,3,7] 表示。在这种情况下，容器能容纳的最大水量（蓝色部分）为 49。
 *   示例 2：输入 height = [1,1]，输出 1。
 *   提示：n == height.length，2 <= n <= 10^5，0 <= height[i] <= 10^4。
 * 思路：
 *   1. 初始化 left 指针指向数组起始位置，right 指针指向数组末尾位置，maxArea 记录最大面积。
 *   2. 计算当前左右指针所围成的面积：面积 = min(height[left], height[right]) * (right - left)，并更新 maxArea。
 *   3. 比较 height[left] 与 height[right]，将高度较小的一端向中间移动一位；因为移动高度较大的一端，容器宽度减小，而高度受限于较小端，面积不可能增大。
 *   4. 重复步骤 2-3，直到 left >= right，最终返回 maxArea。
 * 算法：双指针——从两端向中间收敛，利用单调性减少不必要的枚举。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxArea(height: number[]): number {
    let left = 0;
    let right = height.length - 1;
    let maxArea = 0;
    while (left < right) {
        const h = Math.min(height[left], height[right]);
        maxArea = Math.max(maxArea, h * (right - left));
        if (height[left] < height[right]) {
            left++;
        } else {
            right--;
        }
    }
    return maxArea;
}
