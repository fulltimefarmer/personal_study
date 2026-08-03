/**
 * 考点：数组、动态规划
 * 题目：House Robber（打家劫舍）
 * 题目描述：不能偷相邻房屋，求最大偷窃金额。nums=[1,2,3,1] 输出 4
 * 思路：dp[i]=max(dp[i-1], dp[i-2]+nums[i])，滚动变量优化。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function rob(nums: number[]): number {
    let prev2 = 0;
    let prev1 = 0;

    for (const num of nums) {
        const cur = Math.max(prev1, prev2 + num);
        prev2 = prev1;
        prev1 = cur;
    }

    return prev1;
}
export { rob };
