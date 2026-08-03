/**
 * 考点：Math, Binary Search
 * 题目：Sqrt(x)（x 的平方根）
 * 题目描述：计算非负整数 x 的算术平方根，只保留整数部分，不允许使用内置指数函数。
 * 示例：x = 4 → 2
 * 示例：x = 8 → 2
 * 思路：二分查找。在 [1, x] 范围内找最大的 mid 使得 mid * mid <= x。
 *       用除法 mid <= x/mid 避免溢出。
 * 时间复杂度：O(log x)
 * 空间复杂度：O(1)
 */
function mySqrt(x: number): number {
    if (x < 2) return x;

    let left = 1;
    let right = Math.floor(x / 2);
    let result = 0;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (mid <= x / mid) {
            result = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }

    return result;
}

export { mySqrt };
