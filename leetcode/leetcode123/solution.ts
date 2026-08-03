/**
 * 考点：数组、动态规划
 * 题目：Best Time to Buy and Sell Stock III（买卖股票的最佳时机 III）
 * 题目描述：最多完成两笔交易，求最大利润。不能同时参与多笔交易。
 *   示例：prices = [3,3,5,0,0,3,1,4] → 6
 * 思路：状态机 DP。维护四个状态：buy1, sell1, buy2, sell2。
 *   buy1 = max(buy1, -price)
 *   sell1 = max(sell1, buy1 + price)
 *   buy2 = max(buy2, sell1 - price)
 *   sell2 = max(sell2, buy2 + price)
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function maxProfitIII(prices: number[]): number {
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

export { maxProfitIII };
