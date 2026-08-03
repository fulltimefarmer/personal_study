/**
 * 考点：位运算
 * 题目：Hamming Distance（汉明距离）
 * 题目描述：两个整数之间的汉明距离是两个数字对应二进制位不同的位置的数目。给定 x 和 y，计算汉明距离。
 * 示例：
 *   输入: x=1, y=4 → 输出: 2 (1:0001, 4:0100, 第2位和第4位不同)
 * 思路：计算 x ^ y，然后使用 Brian Kernighan 算法统计异或结果中 1 的个数。
 * 时间复杂度：O(log n)
 * 空间复杂度：O(1)
 */
function hammingDistance(x: number, y: number): number {
    let xor = x ^ y;
    let distance = 0;

    while (xor !== 0) {
        xor &= (xor - 1);
        distance++;
    }

    return distance;
}

export { hammingDistance };
