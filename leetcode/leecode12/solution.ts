/**
 * 考点：Hash Table, Math, String
 * 题目：Integer to Roman（整数转罗马数字）
 * 题目描述：给定一个 1 到 3999 之间的整数，将其转换为罗马数字。
 * 示例：num = 1994 => "MCMXCIV"
 * 思路：贪心算法，预定义所有可能的罗马数字映射（包括特殊规则），从大到小匹配
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 */
function intToRoman(num: number): string {
    const values: number[] = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
    const symbols: string[] = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"];

    let result = "";
    let remaining = num;

    for (let i = 0; i < values.length; i++) {
        while (remaining >= values[i]) {
            result += symbols[i];
            remaining -= values[i];
        }
    }

    return result;
}
export { intToRoman };
