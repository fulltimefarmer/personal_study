/**
 * 考点：Array, Binary Search
 * 题目：Search in Rotated Sorted Array（搜索旋转排序数组）
 * 题目描述：在旋转后的升序数组中搜索目标值，返回下标，不存在返回 -1。
 * 示例：nums = [4,5,6,7,0,1,2], target = 0 => 4
 * 思路：二分查找，每次判断 mid 落在左半有序区间还是右半有序区间，据此调整搜索范围
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function search(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);

        if (nums[mid] === target) {
            return mid;
        }

        if (nums[left] <= nums[mid]) {
            if (nums[left] <= target && target < nums[mid]) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        } else {
            if (nums[mid] < target && target <= nums[right]) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
    }

    return -1;
}
export { search };
