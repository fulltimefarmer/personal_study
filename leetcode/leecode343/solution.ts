/**
 * 考点：数学、动态规划
 * 题目：Integer Break（整数拆分）
 * 题目描述：将 n 拆分为至少两个正整数的和，使乘积最大
 * 思路：数学法。尽可能多拆出 3。
 *       如果 n <= 3 返回 n-1；否则统计 3 的个数，
 *       余 1 时拿出一个 3 和 1 组成 4，余 2 则乘 2。
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function integerBreak(n: number): number {
    if (n <= 3) return n - 1;

    const count3 = Math.floor(n / 3);
    const remainder = n % 3;

    if (remainder === 0) return Math.pow(3, count3);
    if (remainder === 1) return Math.pow(3, count3 - 1) * 4;
    return Math.pow(3, count3) * 2;
}

export { integerBreak };
