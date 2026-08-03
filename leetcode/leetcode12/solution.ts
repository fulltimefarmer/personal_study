/**
 * 考点：Hash Table, Math, String
 * 题目：Integer to Roman（整数转罗马数字）
 * 题目描述：将1-3999的整数转为罗马数字。如 1994 → "MCMXCIV"
 * 思路：贪心。列出所有数值到罗马字符的映射（从大到小），每次用最大可能值去匹配。
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function intToRoman(num: number): string {
    const values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
    const symbols = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'];

    let result = '';
    for (let i = 0; i < values.length; i++) {
        while (num >= values[i]) {
            result += symbols[i];
            num -= values[i];
        }
    }
    return result;
}

export { intToRoman };
