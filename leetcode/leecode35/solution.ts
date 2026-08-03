/**
 * 考点：Array, Binary Search
 * 题目：Search Insert Position（搜索插入位置）
 * 题目描述：在排序数组中搜索目标值，找到返回索引，不存在返回应该插入的位置。
 * 示例：nums = [1,3,5,6], target = 5 => 2
 * 思路：二分查找，找到返回 mid，未找到时 left 指向插入位置
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function searchInsert(nums: number[], target: number): number {
    let left = 0;
    let right = nums.length - 1;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);

        if (nums[mid] === target) {
            return mid;
        } else if (nums[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }

    return left;
}
export { searchInsert };
