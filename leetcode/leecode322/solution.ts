/**
 * 考点：BFS、数组、动态规划
 * 题目：Coin Change（零钱兑换）
 * 题目描述：给定硬币面额和总金额，求所需最少硬币数，无解返回 -1
 * 思路：动态规划（完全背包）。dp[i] = min(dp[i - coin] + 1)
 * 时间复杂度：O(amount × n)
 * 空间复杂度：O(amount)
 */
function coinChange(coins: number[], amount: number): number {
    const dp = new Array(amount + 1).fill(Infinity);
    dp[0] = 0;

    for (let i = 1; i <= amount; i++) {
        for (const coin of coins) {
            if (coin <= i) {
                dp[i] = Math.min(dp[i], dp[i - coin] + 1);
            }
        }
    }

    return dp[amount] === Infinity ? -1 : dp[amount];
}

export { coinChange };
