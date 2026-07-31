/**
 * 考点：Dynamic Programming、Memoization
 * 题目：Climbing Stairs
 * 题目描述：假设你正在爬楼梯。需要 n 阶你才能到达楼顶。
 *          每次你可以爬 1 或 2 个台阶。你有多少种不同的方法可以爬到楼顶呢？
 *          注意：给定 n 是一个正整数。
 *          示例：输入 n = 3，输出 3；解释：共有 3 种方法：1+1+1、1+2、2+1。
 * 思路：第一步：推导状态转移方程：到达第 n 级只能从第 n-1 级迈 1 步或从第 n-2 级迈 2 步，
 *              因此 f(n) = f(n-1) + f(n-2)。
 *       第二步：边界处理：n <= 2 时直接返回 n。
 *       第三步：初始化 prev2 = 1（f(1)）、prev1 = 2（f(2)）。
 *       第四步：从 i = 3 到 n 循环，计算 cur = prev1 + prev2，并滚动更新 prev2 = prev1、prev1 = cur。
 *       第五步：返回 prev1，得到爬到第 n 级的方法总数。
 * 算法：动态规划（滚动数组优化）。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
public class Solution {
    public int climbStairs(int n) {
        if (n <= 2) return n;
        int prev2 = 1; // f(n-2)
        int prev1 = 2; // f(n-1)
        for (int i = 3; i <= n; i++) {
            int cur = prev1 + prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
}
