/**
 * 考点：Array, Dynamic Programming
 * 题目：Best Time to Buy and Sell Stock III（买卖股票的最佳时机III）
 * 题目描述：最多完成两笔交易，求最大利润（不能同时持有多股）。
 * 示例 1：[3,3,5,0,0,3,1,4]，输出 6（0→3 + 1→4）
 * 示例 2：[1,2,3,4,5]，输出 4
 * 示例 3：[7,6,4,3,1]，输出 0
 * 思路：状态机 DP，buy1/sell1/buy2/sell2 四个状态。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProfit3(prices: number[]): number {
    let buy1 = -Infinity;
    let sell1 = 0;
    let buy2 = -Infinity;
    let sell2 = 0;

    for (const price of prices) {
        buy1 = Math.max(buy1, -price);
        sell1 = Math.max(sell1, buy1 + price);
        buy2 = Math.max(buy2, sell1 - price);
        sell2 = Math.max(sell2, buy2 + price);
    }

    return sell2;
}

export { maxProfit3 };
