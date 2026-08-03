/**
 * 考点：Array, Math
 * 题目：Plus One（加一）
 * 题目描述：给定由整数数组表示的非负整数，加一后返回新的数组。
 * 示例：digits = [1,2,3] → [1,2,4]
 * 示例：digits = [9] → [1,0]
 * 思路：从末尾向前遍历，若 digits[i] < 9 则加一返回；若为 9 则置零并进位。
 *       若遍历完所有位都是 9，则在开头插入 1。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)（最坏 O(n)，当全为 9 时）
 */
function plusOne(digits: number[]): number[] {
    for (let i = digits.length - 1; i >= 0; i--) {
        if (digits[i] < 9) {
            digits[i]++;
            return digits;
        }
        digits[i] = 0;
    }

    digits.unshift(1);
    return digits;
}

export { plusOne };
