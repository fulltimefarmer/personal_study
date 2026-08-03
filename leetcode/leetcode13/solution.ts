/**
 * 考点：Hash Table, Math, String
 * 题目：Roman to Integer（罗马数字转整数）
 * 题目描述：将罗马数字字符串转为整数。如 "MCMXCIV" → 1994
 * 思路：遍历字符串，当前值小于下一值则减去（如IV中I），否则加上。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function romanToInt(s: string): number {
    const map: Record<string, number> = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000,
    };

    let result = 0;
    for (let i = 0; i < s.length; i++) {
        const cur = map[s[i]];
        const next = i + 1 < s.length ? map[s[i + 1]] : 0;
        if (cur < next) {
            result -= cur;
        } else {
            result += cur;
        }
    }
    return result;
}

export { romanToInt };
