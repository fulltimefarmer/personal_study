/**
 * 考点：Recursion, Math
 * 题目：Pow(x, n)（Pow(x, n)）
 * 题目描述：实现 pow(x, n)，计算 x 的整数 n 次幂 x^n。
 * 示例：x = 2.00000, n = 10 → 1024.00000
 * 示例：x = 2.00000, n = -2 → 0.25000
 * 思路：快速幂（二分法）。n 为偶数时 x^n = (x^2)^(n/2)，奇数时 x^n = x * (x^2)^(n/2)。
 *       迭代实现避免栈溢出，处理 n 为负数时转 1/pow(x,-n)，注意 n = -2^31 的溢出问题。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function myPow(x: number, n: number): number {
    if (n === 0) return 1;

    let N = n;
    if (N < 0) {
        x = 1 / x;
        if (N === -(2 ** 31)) {
            N = -(N + 1);
            x = x / x; // 多除一次 x 补偿
            N = N + 1;
        } else {
            N = -N;
        }
    }

    let result = 1;
    let current = x;
    while (N > 0) {
        if (N % 2 === 1) {
            result *= current;
        }
        current *= current;
        N = Math.floor(N / 2);
    }
    return result;
}

export { myPow };
