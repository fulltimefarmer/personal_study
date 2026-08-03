/**
 * 考点：Greedy, Array, Dynamic Programming
 * 题目：Best Time to Buy and Sell Stock II（买卖股票的最佳时机II）
 * 题目描述：允许多次交易（同一天可买卖），求最大总利润。
 * 示例 1：[7,1,5,3,6,4]，输出 7（1→5 得 4 + 3→6 得 3）
 * 示例 2：[1,2,3,4,5]，输出 4
 * 示例 3：[7,6,4,3,1]，输出 0
 * 思路：贪心，累加所有 prices[i] > prices[i-1] 的差值。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProfit2(prices: number[]): number {
    let profit = 0;

    for (let i = 1; i < prices.length; i++) {
        if (prices[i] > prices[i - 1]) {
            profit += prices[i] - prices[i - 1];
        }
    }

    return profit;
}

export { maxProfit2 };
