/**
 * 考点：贪心, 数组, 动态规划
 * 题目：Best Time to Buy and Sell Stock with Transaction Fee（买卖股票的最佳时机含手续费）
 * 题目描述：给定 prices[i] 和手续费 fee，可无限次交易，但每次卖出需支付 fee。求最大利润。
 * 示例：
 *   输入: prices=[1,3,2,8,4,9], fee=2 → 输出: 8
 * 思路：DP。两个状态：hold（持有股票最大收益），cash（不持有最大收益）。cash=max(cash, hold+prices[i]-fee)；hold=max(hold, cash-prices[i])。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProfit(prices: number[], fee: number): number {
    let hold = -prices[0];
    let cash = 0;

    for (let i = 1; i < prices.length; i++) {
        cash = Math.max(cash, hold + prices[i] - fee);
        hold = Math.max(hold, cash - prices[i]);
    }

    return cash;
}

export { maxProfit };
