/**
 * 考点：数组、动态规划
 * 题目：Arithmetic Slices（等差数列划分）
 * 题目描述：统计数组中所有等差子数组（连续、长度 >= 3）的个数
 * 思路：DP。若 nums[i]-nums[i-1] == nums[i-1]-nums[i-2]，
 *       dp = dp + 1（所有以 i-1 结尾的等差子数组可接上 i，再加新的三元组）
 *       累加 dp 到总结果。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function numberOfArithmeticSlices(nums: number[]): number {
    if (nums.length < 3) return 0;

    let dp = 0;
    let result = 0;

    for (let i = 2; i < nums.length; i++) {
        if (nums[i] - nums[i - 1] === nums[i - 1] - nums[i - 2]) {
            dp = dp + 1;
            result += dp;
        } else {
            dp = 0;
        }
    }

    return result;
}

export { numberOfArithmeticSlices };
