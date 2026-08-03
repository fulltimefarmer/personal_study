/**
 * 考点：Array, Binary Search
 * 题目：Search in Rotated Sorted Array（搜索旋转排序数组）
 * 题目描述：在旋转后的有序数组中搜索target。如 [4,5,6,7,0,1,2], target=0 → 4
 * 思路：二分查找，通过比较nums[mid]和nums[left]判断哪侧有序，在有序侧判断target范围。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function search(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;

    while (left <= right) {
        const mid = (left + right) >> 1;
        if (nums[mid] === target) return mid;

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
