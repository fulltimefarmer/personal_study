/**
 * 考点：Array, Binary Search
 * 题目：Search Insert Position（搜索插入位置）
 * 题目描述：在有序数组中找target，找不到则返回应插入的位置。如 [1,3,5,6], 2 → 1
 * 思路：标准二分查找，找到返回mid，未找到时left就是插入位置。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function searchInsert(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;

    while (left <= right) {
        const mid = (left + right) >> 1;
        if (nums[mid] === target) return mid;
        if (nums[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }

    return left;
}

export { searchInsert };
