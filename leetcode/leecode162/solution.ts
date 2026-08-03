/**
 * 考点：Array, Binary Search
 * 题目：Find Peak Element（寻找峰值）
 * 题目描述：找任意一个峰值（大于左右相邻值），nums[-1]=nums[n]=-∞，O(log n)。
 * 示例 1：[1,2,3,1]，输出 2（峰值 3）
 * 示例 2：[1,2,1,3,5,6,4]，输出 1 或 5
 * 思路：二分查找，比较 nums[mid] 和 nums[mid+1]。
 * nums[mid]>nums[mid+1] → 下降，左侧有峰值 → right=mid
 * nums[mid]<nums[mid+1] → 上升，右侧有峰值 → left=mid+1
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function findPeakElement(nums: number[]): number {
    let left = 0;
    let right = nums.length - 1;

    while (left < right) {
        const mid = Math.floor((left + right) / 2);
        if (nums[mid] > nums[mid + 1]) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }

    return left;
}

export { findPeakElement };
