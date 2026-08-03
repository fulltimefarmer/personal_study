/**
 * 考点：数组, 动态规划
 * 题目：Coin Change II（零钱兑换II）
 * 题目描述：给定硬币面额 coins 和总金额 amount，求凑成总金额的硬币组合数。每种硬币无限使用。
 * 示例：
 *   输入: amount=5, coins=[1,2,5] → 输出: 4
 * 思路：完全背包求组合数。dp[j] 表示金额 j 的组合数。外层硬币、内层金额正序：dp[j] += dp[j-coin]。
 * 时间复杂度：O(n * amount)
 * 空间复杂度：O(amount)
 */
function change(amount: number, coins: number[]): number {
    const dp: number[] = new Array(amount + 1).fill(0);
    dp[0] = 1;

    for (const coin of coins) {
        for (let j = coin; j <= amount; j++) {
            dp[j] += dp[j - coin];
        }
    }

    return dp[amount];
}

export { change };
