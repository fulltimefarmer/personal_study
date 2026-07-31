/**
 * 考点：Dynamic Programming
 * 题目：Coin Change（零钱兑换）
 * 题目描述：
 *   给你一个整数数组 coins，表示不同面额的硬币；以及一个整数 amount，表示总金额。
 *   计算并返回可以凑成总金额所需的 最少硬币个数。如果没有任何一种硬币组合能组成总金额，返回 -1。
 *   你可以认为每种硬币的数量是无限的。
 *   示例 1：
 *   输入：coins = [1,2,5], amount = 11
 *   输出：3
 *   解释：11 = 5 + 5 + 1
 *   示例 2：
 *   输入：coins = [2], amount = 3
 *   输出：-1
 *   示例 3：
 *   输入：coins = [1], amount = 0
 *   输出：0
 *   提示：
 *   - 1 <= coins.length <= 12
 *   - 1 <= coins[i] <= 2^31 - 1
 *   - 0 <= amount <= 10^4
 * 思路：
 *   1. 定义 dp[i] 为凑成金额 i 所需的最少硬币数。
 *   2. 初始化：dp[0] = 0（金额 0 不需要硬币），其余 dp[i] 初始化为 amount + 1（一个不可能超过的最大值），表示暂不可达。
 *   3. 外层遍历金额 i 从 1 到 amount；内层遍历每枚硬币 coin。
 *   4. 若 coin <= i，则 dp[i] = min(dp[i], dp[i - coin] + 1)。
 *   5. 最终若 dp[amount] 仍大于 amount，说明无法凑出，返回 -1；否则返回 dp[amount]。
 * 算法：完全背包 —— 硬币数量无限，每个金额可以被任意硬币更新。
 * 时间复杂度：O(amount * n)
 * 空间复杂度：O(amount)
 */
public class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        for (int i = 1; i <= amount; i++) {
            dp[i] = amount + 1;
        }
        dp[0] = 0;

        for (int i = 1; i <= amount; i++) {
            for (int coin : coins) {
                if (i - coin >= 0) {
                    dp[i] = Math.min(dp[i], dp[i - coin] + 1);
                }
            }
        }

        return dp[amount] > amount ? -1 : dp[amount];
    }
}
