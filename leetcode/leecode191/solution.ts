/**
 * 考点：位运算、分治
 * 题目：Number of 1 Bits（位1的个数）
 * 题目描述：返回无符号整数二进制表示中 1 的个数（汉明重量）。
 * 示例：n=00000000000000000000000000001011 输出 3
 * 思路：n & (n-1) 消除最低位的 1，计数直到 n 为 0。
 * 时间复杂度：O(k)，k 为 1 的个数
 * 空间复杂度：O(1)
 */
function hammingWeight(n: number): number {
    let count = 0;
    while (n !== 0) {
        n &= n - 1;
        count++;
    }
    return count;
}
export { hammingWeight };
