/**
 * 考点：数组、动态规划
 * 题目：Best Time to Buy and Sell Stock with Cooldown（最佳买卖股票时机含冷冻期）
 * 题目描述：多次买卖股票，卖出后有一天冷冻期，求最大利润
 * 思路：DP 三状态。持有/当天卖出(冷冻)/不持有不冷冻。
 *       dp0 = max(dp0, dp2 - price)，dp1 = dp0 + price，dp2 = max(dp1, dp2)
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProfit(prices: number[]): number {
    let dp0 = -Infinity;
    let dp1 = 0;
    let dp2 = 0;

    for (const price of prices) {
        const newDp0 = Math.max(dp0, dp2 - price);
        const newDp1 = dp0 + price;
        const newDp2 = Math.max(dp1, dp2);
        dp0 = newDp0;
        dp1 = newDp1;
        dp2 = newDp2;
    }

    return Math.max(dp1, dp2);
}

export { maxProfit };
