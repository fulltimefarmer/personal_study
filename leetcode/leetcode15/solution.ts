/**
 * 考点：Array, Two Pointers, Sorting
 * 题目：3Sum（三数之和）
 * 题目描述：找数组中所有不重复的三元组，使和为0。如 [-1,0,1,2,-1,-4] → [[-1,-1,2],[-1,0,1]]
 * 思路：排序后固定一个数，双指针在剩余部分找两数之和。注意跳过重复值。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(1)（不计结果存储）
 */
function threeSum(nums: number[]): number[][] {
    nums.sort((a, b) => a - b);
    const result: number[][] = [];
    const n = nums.length;

    for (let i = 0; i < n - 2; i++) {
        if (nums[i] > 0) break;
        if (i > 0 && nums[i] === nums[i - 1]) continue;

        let left = i + 1;
        let right = n - 1;

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
