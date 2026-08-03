/**
 * 考点：Array, Dynamic Programming
 * 题目：Best Time to Buy and Sell Stock（买卖股票的最佳时机）
 * 题目描述：给定股票价格数组，只能买卖一次，求最大利润。不能获取利润返回 0。
 * 示例 1：[7,1,5,3,6,4]，输出 5（1 买入，6 卖出）
 * 示例 2：[7,6,4,3,1]，输出 0（没有交易）
 * 思路：遍历维护最低价格，计算每天卖出可得的最大利润。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProfit(prices: number[]): number {
    let minPrice = Infinity;
    let maxProfit = 0;

    for (const price of prices) {
        if (price < minPrice) {
            minPrice = price;
        } else {
            maxProfit = Math.max(maxProfit, price - minPrice);
        }
    }

    return maxProfit;
}

export { maxProfit };
