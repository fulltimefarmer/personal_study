/**
 * 考点：数组、动态规划
 * 题目：Best Time to Buy and Sell Stock IV（买卖股票的最佳时机 IV）
 * 题目描述：最多完成 k 笔交易，求最大利润。k=2,prices=[3,2,6,5,0,3] 输出 7。
 * 思路：DP，dp[i][j] 表示前 j 天最多 i 次交易的最大利润。maxPrev 维护 dp[i-1][j-1]-prices[j-1] 的最大值。
 *       若 k>=n/2，可以无限交易，累加正利润。
 * 时间复杂度：O(k × n)
 * 空间复杂度：O(n)
 */
function maxProfitIV(k: number, prices: number[]): number {
    const n = prices.length;
    if (n === 0) return 0;

    if (k >= Math.floor(n / 2)) {
        let profit = 0;
        for (let i = 1; i < n; i++) {
            if (prices[i] > prices[i - 1]) {
                profit += prices[i] - prices[i - 1];
            }
        }
        return profit;
    }

    const dp: number[] = new Array(n).fill(0);

    for (let i = 1; i <= k; i++) {
        let maxPrev = -prices[0];
        let prevProfit = 0;
        for (let j = 1; j < n; j++) {
            const temp = dp[j];
            dp[j] = Math.max(dp[j - 1], prices[j] + maxPrev);
            maxPrev = Math.max(maxPrev, prevProfit - prices[j]);
            prevProfit = temp;
        }
    }

    return dp[n - 1];
}
export { maxProfitIV };
