/**
 * 考点：数组、二分查找
 * 题目：Find Minimum in Rotated Sorted Array（寻找旋转排序数组中的最小值）
 * 题目描述：一个升序数组经过旋转后，找到最小元素。元素互不相同。要求 O(log n)。
 *   示例：nums = [3,4,5,1,2] → 1
 * 思路：二分查找。比较 nums[mid] 和 nums[right]：
 *   nums[mid] > nums[right] → 最小值在右边，left = mid + 1
 *   nums[mid] < nums[right] → 最小值在左边或就是 mid，right = mid
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
