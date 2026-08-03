/**
 * 考点：Hash Table, Math, String
 * 题目：Roman to Integer（罗马数字转整数）
 * 题目描述：给定一个罗马数字字符串，将其转换成整数。
 * 示例：s = "MCMXCIV" => 1994
 * 思路：从左到右遍历，如果当前字符值小于后一个字符值则减去，否则加上
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function romanToInt(s: string): number {
    const map: Record<string, number> = {
        I: 1,
        V: 5,
        X: 10,
        L: 50,
        C: 100,
        D: 500,
        M: 1000,
    };

    let result = 0;

    for (let i = 0; i < s.length; i++) {
        const current = map[s[i]];
        const next = map[s[i + 1]];

        if (current < next) {
            result -= current;
        } else {
            result += current;
        }
    }

    return result;
}
export { romanToInt };
