/**
 * 考点：递归, 记忆化搜索, 数学, 动态规划
 * 题目：Fibonacci Number（斐波那契数）
 * 题目描述：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)（n>1）。给定 n，计算 F(n)。
 * 示例：
 *   输入: n=2 → 输出: 1
 *   输入: n=4 → 输出: 3
 * 思路：动态规划迭代法。用两个变量 prev2 和 prev1 分别保存 F(n-2) 和 F(n-1)，迭代计算即可。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function fib(n: number): number {
    if (n <= 1) return n;

    let prev2 = 0;
    let prev1 = 1;

    for (let i = 2; i <= n; i++) {
        const curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }

    return prev1;
}

export { fib };
