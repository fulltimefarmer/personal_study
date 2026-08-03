/**
 * 考点：Array, Binary Search
 * 题目：Find Minimum in Rotated Sorted Array（寻找旋转排序数组中的最小值）
 * 题目描述：旋转过的升序数组（无重复），找最小值，O(log n)。
 * 示例 1：[3,4,5,1,2]，输出 1
 * 示例 2：[4,5,6,7,0,1,2]，输出 0
 * 示例 3：[11,13,15,17]，输出 11
 * 思路：二分查找，比较 nums[mid] 和 nums[right]。
 * nums[mid]>nums[right] → 最小值在右，left=mid+1
 * nums[mid]<nums[right] → 最小值在左（含 mid），right=mid
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function findMin(nums: number[]): number {
    let left = 0;
    let right = nums.length - 1;

    while (left < right) {
        const mid = Math.floor((left + right) / 2);
        if (nums[mid] > nums[right]) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }

    return nums[left];
}

export { findMin };
