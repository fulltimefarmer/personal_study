/**
 * 考点：动态规划
 * 题目：Domino and Tromino Tiling（多米诺和托米诺平铺）
 * 题目描述：用 2x1 多米诺和 L 形托米诺平铺 2xn 面板，求方案数 mod 10^9+7。
 * 示例：
 *   输入: n=3 → 输出: 5
 * 思路：DP。递推公式：dp[i] = 2 * dp[i-1] + dp[i-3]（i>=3）。dp[0]=1, dp[1]=1, dp[2]=2。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function numTilings(n: number): number {
    const MOD = 1e9 + 7;

    if (n === 1) return 1;
    if (n === 2) return 2;

    let dp0 = 1;
    let dp1 = 1;
    let dp2 = 2;
    let dp3 = 0;

    for (let i = 3; i <= n; i++) {
        dp3 = (2 * dp2 + dp0) % MOD;
        dp0 = dp1;
        dp1 = dp2;
        dp2 = dp3;
    }

    return dp2;
}

export { numTilings };
