/**
 * 考点：Array, Two Pointers, Sorting
 * 题目：3Sum（三数之和）
 * 题目描述：找出数组中所有和为 0 且不重复的三元组。
 * 示例：nums = [-1,0,1,2,-1,-4] => [[-1,-1,2],[-1,0,1]]
 * 思路：排序 + 双指针，固定第一个数，双指针在剩余区间找两数之和为 -nums[i]，去重
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(1)
 */
function threeSum(nums: number[]): number[][] {
    nums.sort((a, b) => a - b);
    const result: number[][] = [];

    for (let i = 0; i < nums.length - 2; i++) {
        if (nums[i] > 0) break;
        if (i > 0 && nums[i] === nums[i - 1]) continue;

        let left = i + 1;
        let right = nums.length - 1;

        while (left < right) {
            const sum = nums[i] + nums[left] + nums[right];

            if (sum === 0) {
                result.push([nums[i], nums[left], nums[right]]);
                while (left < right && nums[left] === nums[left + 1]) left++;
                while (left < right && nums[right] === nums[right - 1]) right--;
                left++;
                right--;
            } else if (sum < 0) {
                left++;
            } else {
                right--;
            }
        }
    }

    return result;
}
export { threeSum };
