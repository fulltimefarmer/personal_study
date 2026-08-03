/**
 * 考点：Math, Dynamic Programming, Memoization
 * 题目：Climbing Stairs（爬楼梯）
 * 题目描述：爬 n 阶楼梯，每次爬 1 或 2 阶，求不同方法数。
 * 示例：n = 2 → 2
 * 示例：n = 3 → 3
 * 思路：斐波那契数列。dp[n] = dp[n-1] + dp[n-2]，空间优化为 O(1)。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function climbStairs(n: number): number {
    if (n <= 2) return n;

    let prev2 = 1;
    let prev1 = 2;

    for (let i = 3; i <= n; i++) {
        const current = prev1 + prev2;
        prev2 = prev1;
        prev1 = current;
    }

    return prev1;
}

export { climbStairs };
