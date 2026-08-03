/**
 * 考点：栈, 贪心, 数组, 双指针, 排序, 单调栈
 * 题目：Shortest Unsorted Continuous Subarray（最短无序连续子数组）
 * 题目描述：给定 nums，找出最短的连续子数组，排序后整个数组变为升序。返回子数组长度。
 * 示例：
 *   输入: [2,6,4,8,10,9,15] → 输出: 5 (子数组[6,4,8,10,9])
 * 思路：一次遍历。从左到右找右边界（遇到比max小的更新right），从右到左找左边界（遇到比min大的更新left）。right-left+1即为结果。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function findUnsortedSubarray(nums: number[]): number {
    const n = nums.length;
    let max = -Infinity;
    let min = Infinity;
    let left = -1;
    let right = -1;

    for (let i = 0; i < n; i++) {
        if (nums[i] < max) {
            right = i;
        } else {
            max = nums[i];
        }
    }

    for (let i = n - 1; i >= 0; i--) {
        if (nums[i] > min) {
            left = i;
        } else {
            min = nums[i];
        }
    }

    return right <= left ? 0 : right - left + 1;
}

export { findUnsortedSubarray };
