/**
 * 考点：Two Pointers、Sorting
 * 题目：3Sum
 * 题目描述：
 *   给你一个整数数组 nums，判断是否存在三元组 [nums[i], nums[j], nums[k]] 满足 i != j、i != k 且 j != k，同时还满足 nums[i] + nums[j] + nums[k] == 0。
 *   请你返回所有和为 0 且不重复的三元组。
 *   注意：答案中不可以包含重复的三元组。
 *   示例 1：输入 nums = [-1,0,1,2,-1,-4]，输出 [[-1,-1,2],[-1,0,1]]。
 *   示例 2：输入 nums = [0,1,1]，输出 []。解释：唯一可能的三元组和不为 0。
 *   示例 3：输入 nums = [0,0,0]，输出 [[0,0,0]]。
 *   提示：3 <= nums.length <= 3000，-10^5 <= nums[i] <= 10^5。
 * 思路：
 *   1. 先对数组 nums 进行排序，便于使用双指针并跳过重复值。
 *   2. 枚举第一个数 i，范围从 0 到 nums.length - 3：
 *      a) 如果 i > 0 且 nums[i] == nums[i - 1]，跳过该位置，避免三元组重复。
 *   3. 在剩余区间 [i + 1, nums.length - 1] 内使用双指针 left、right：
 *      a) 计算 sum = nums[i] + nums[left] + nums[right]。
 *      b) 若 sum == 0，记录该三元组，并将 left 右移直到下一个不同的值，right 左移直到下一个不同的值，然后两指针同时向中间移动。
 *      c) 若 sum < 0，说明需要更大的数，left++。
 *      d) 若 sum > 0，说明需要更小的数，right--。
 *   4. 所有记录下来的三元组即为答案。
 * 算法：排序 + 双指针——排序后利用有序性，通过双指针从两端向中间收缩查找目标和。
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(1)（不考虑排序栈空间，取决于语言实现）
 */
function threeSum(nums: number[]): number[][] {
    const result: number[][] = [];
    nums.sort((a, b) => a - b);
    for (let i = 0; i < nums.length - 2; i++) {
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
