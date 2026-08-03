/**
 * 考点：数学
 * 题目：Factorial Trailing Zeroes（阶乘后的零）
 * 题目描述：给定整数 n，返回 n! 结果中尾随零的数量。尾随零由因子 10=2×5 产生，2 的数量总是多于 5，因此只需计算因子 5 的数量。
 * 示例：n=5 输出 1（5!=120），n=3 输出 0
 * 思路：不断将 n 除以 5，累加商，即 n/5 + n/25 + n/125 + ...
 * 时间复杂度：O(log₅ n)
 * 空间复杂度：O(1)
 */
function trailingZeroes(n: number): number {
    let count = 0;
    while (n >= 5) {
        n = Math.floor(n / 5);
        count += n;
    }
    return count;
}
export { trailingZeroes };
