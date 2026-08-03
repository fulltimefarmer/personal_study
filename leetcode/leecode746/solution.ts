/**
 * 考点：数组, 动态规划
 * 题目：Min Cost Climbing Stairs（使用最小花费爬楼梯）
 * 题目描述：cost[i] 是从第 i 阶向上爬的花费，每次可爬 1 或 2 阶。可从第 0 或第 1 阶开始。求到达顶部的最小花费。
 * 示例：
 *   输入: [10,15,20] → 输出: 15
 *   输入: [1,100,1,1,1,100,1,1,100,1] → 输出: 6
 * 思路：DP。dp[i]=cost[i]+min(dp[i-1], dp[i-2])。答案为 min(dp[n-1], dp[n-2])。用两个变量滚动优化空间。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function minCostClimbingStairs(cost: number[]): number {
    const n = cost.length;
    let prev2 = cost[0];
    let prev1 = cost[1];

    for (let i = 2; i < n; i++) {
        const curr = cost[i] + Math.min(prev1, prev2);
        prev2 = prev1;
        prev1 = curr;
    }

    return Math.min(prev1, prev2);
}

export { minCostClimbingStairs };
