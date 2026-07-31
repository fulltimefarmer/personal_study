/**
 * 考点：Dynamic Programming、Memoization
 * 题目：Climbing Stairs
 * 题目描述：假设你正在爬楼梯。需要 n 阶你才能到达楼顶。
 *          每次你可以爬 1 或 2 个台阶。你有多少种不同的方法可以爬到楼顶呢？
 *          注意：给定 n 是一个正整数。
 *          示例：输入 n = 3，输出 3；解释：共有 3 种方法：1+1+1、1+2、2+1。
 * 思路：第一步：分析问题，爬到第 n 级台阶的最后一步只可能来自第 n-1 级（迈 1 步）或第 n-2 级（迈 2 步）。
 *              因此方法数满足 f(n) = f(n-1) + f(n-2)，即斐波那契数列。
 *       第二步：处理边界：n <= 2 时直接返回 n（n=1 有一种，n=2 有两种）。
 *       第三步：使用滚动变量 prev2（f(n-2)）和 prev1（f(n-1)）保存前两个状态，避免使用数组。
 *       第四步：从 i = 3 循环到 n，计算 cur = prev1 + prev2，然后滚动更新 prev2 = prev1、prev1 = cur。
 *       第五步：返回 prev1，即为爬到第 n 级台阶的方法总数。
 * 算法：动态规划（滚动数组优化）。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function climbStairs(n: number): number {
    if (n <= 2) return n;
    let prev2 = 1; // f(n-2)
    let prev1 = 2; // f(n-1)
    for (let i = 3; i <= n; i++) {
        const cur = prev1 + prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
