/**
 * 考点：数组、动态规划
 * 题目：Best Time to Buy and Sell Stock（买卖股票的最佳时机）
 * 题目描述：只能进行一次买卖交易，求最大利润。如果无法获利返回 0。
 *   示例：prices = [7,1,5,3,6,4] → 5（在价格 1 买入，价格 6 卖出）
 * 思路：一次遍历。维护最低价格 minPrice 和最大利润 maxProfit，
 *   每天计算当天卖出能获得的利润并更新最大值。
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
