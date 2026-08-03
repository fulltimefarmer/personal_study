/**
 * 考点：贪心、数组、动态规划
 * 题目：Best Time to Buy and Sell Stock II（买卖股票的最佳时机 II）
 * 题目描述：可以多次买卖，但最多持有一股。求最大利润。
 *   示例：prices = [7,1,5,3,6,4] → 7
 * 思路：贪心。只要今天价格比昨天高就累加利润，因为可以捕捉所有上涨区间。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function maxProfitII(prices: number[]): number {
  let maxProfit = 0;

  for (let i = 1; i < prices.length; i++) {
    if (prices[i] > prices[i - 1]) {
      maxProfit += prices[i] - prices[i - 1];
    }
  }

  return maxProfit;
}

export { maxProfitII };
