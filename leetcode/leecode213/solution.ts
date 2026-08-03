/**
 * 考点：数组、动态规划
 * 题目：House Robber II（打家劫舍 II）
 * 题目描述：房屋围成一圈（首尾相邻），不能偷相邻房间，求最大金额。nums=[2,3,2] 输出 3
 * 思路：分两种情况——不偷第一间（nums[1..]）和不偷最后一间（nums[..n-2]），分别用 House Robber I 的 DP，取最大值。
 *       特殊情况 n=1 直接返回 nums[0]。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function robII(nums: number[]): number {
    const n = nums.length;
    if (n === 1) return nums[0];

    const robRange = (start: number, end: number): number => {
        let prev2 = 0;
        let prev1 = 0;
        for (let i = start; i <= end; i++) {
            const cur = Math.max(prev1, prev2 + nums[i]);
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    };

    return Math.max(robRange(0, n - 2), robRange(1, n - 1));
}
export { robII };
