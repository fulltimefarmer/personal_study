/**
 * 考点：位运算、分治
 * 题目：Reverse Bits（颠倒二进制位）
 * 题目描述：颠倒给定的 32 位无符号整数的二进制位。
 * 示例：n=00000010100101000001111010011100 输出 964176192(00111001011110000010100101000000)
 * 思路：逐位反转，result 左移 + n&1，n 右移，循环 32 次。或用分治法交换相邻位。
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function reverseBits(n: number): number {
    let result = 0;
    for (let i = 0; i < 32; i++) {
        result = (result << 1) | (n & 1);
        n >>>= 1;
    }
    return result >>> 0;
}
export { reverseBits };
