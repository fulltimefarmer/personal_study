/**
 * 考点：Array, Binary Search
 * 题目：Find First and Last Position of Element in Sorted Array（在排序数组中查找元素的第一个和最后一个位置）
 * 题目描述：在有序数组中找target的起始和结束位置。如 [5,7,7,8,8,10], 8 → [3,4]
 * 思路：两次二分，分别找左边界和右边界。找左边界时>=target收缩right，找右边界时<=target收缩left。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function searchRange(nums: number[], target: number): number[] {
    function findLeft(): number {
        let left = 0;
        let right = nums.length - 1;
        while (left <= right) {
            const mid = (left + right) >> 1;
            if (nums[mid] >= target) {
                right = mid - 1;
            } else {
                left = mid + 1;
            }
        }
        return left < nums.length && nums[left] === target ? left : -1;
    }

    function findRight(): number {
        let left = 0;
        let right = nums.length - 1;
        while (left <= right) {
            const mid = (left + right) >> 1;
            if (nums[mid] <= target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return right >= 0 && nums[right] === target ? right : -1;
    }

    return [findLeft(), findRight()];
}

export { searchRange };
