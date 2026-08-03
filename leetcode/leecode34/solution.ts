/**
 * 考点：Array, Binary Search
 * 题目：Find First and Last Position of Element in Sorted Array（在排序数组中查找元素的第一个和最后一个位置）
 * 题目描述：在非递减数组中找出目标值的开始和结束位置，不存在返回 [-1, -1]。
 * 示例：nums = [5,7,7,8,8,10], target = 8 => [3,4]
 * 思路：两次二分查找，分别找起始位置（相等时向左缩）和结束位置（相等时向右缩）
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function searchRange(nums: number[], target: number): number[] {
    const findFirst = (): number => {
        let left = 0;
        let right = nums.length - 1;
        let result = -1;

        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            if (nums[mid] === target) {
                result = mid;
                right = mid - 1;
            } else if (nums[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }

        return result;
    };

    const findLast = (): number => {
        let left = 0;
        let right = nums.length - 1;
        let result = -1;

        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            if (nums[mid] === target) {
                result = mid;
                left = mid + 1;
            } else if (nums[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }

        return result;
    };

    return [findFirst(), findLast()];
}
export { searchRange };
