/**
 * 考点：数组、二分查找
 * 题目：Find Peak Element（寻找峰值）
 * 题目描述：找到一个峰值元素的索引。峰值元素严格大于相邻元素。nums[-1] = nums[n] = -∞。
 *   示例：nums = [1,2,3,1] → 2（值为 3）
 * 思路：二分查找。比较 nums[mid] 和 nums[mid+1]：
 *   nums[mid] > nums[mid+1] → 峰值在左侧（含 mid），right = mid
 *   nums[mid] < nums[mid+1] → 峰值在右侧，left = mid + 1
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
