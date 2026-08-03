/**
 * 考点：Hash Table, String, Backtracking
 * 题目：Letter Combinations of a Phone Number（电话号码的字母组合）
 * 题目描述：给定仅包含 2-9 的数字字符串，返回所有可能的字母组合。
 * 示例：digits = "23" => ["ad","ae","af","bd","be","bf","cd","ce","cf"]
 * 思路：回溯法，建立数字到字母映射，逐位构建组合
 * 时间复杂度：O(3^m * 4^n)
 * 空间复杂度：O(m + n)
 */
function letterCombinations(digits: string): string[] {
    if (digits.length === 0) return [];

    const map: Record<string, string> = {
        "2": "abc",
        "3": "def",
        "4": "ghi",
        "5": "jkl",
        "6": "mno",
        "7": "pqrs",
        "8": "tuv",
        "9": "wxyz",
    };

    const result: string[] = [];

    function backtrack(index: number, current: string): void {
        if (index === digits.length) {
            result.push(current);
            return;
        }

        const letters = map[digits[index]];
        for (const letter of letters) {
            backtrack(index + 1, current + letter);
        }
    }

    backtrack(0, "");
    return result;
}
export { letterCombinations };
