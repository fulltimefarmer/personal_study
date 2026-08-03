/**
 * 考点：Hash Table, String, Backtracking
 * 题目：Letter Combinations of a Phone Number（电话号码的字母组合）
 * 题目描述：给定2-9数字字符串，返回所有可能的字母组合。如 "23" → ["ad","ae","af","bd","be","bf","cd","ce","cf"]
 * 思路：回溯/DFS，遍历每个数字对应的字母，递归构建所有组合。
 * 时间复杂度：O(4^n)
 * 空间复杂度：O(n)
 */
function letterCombinations(digits: string): string[] {
    if (digits.length === 0) return [];

    const map: Record<string, string> = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz',
    };

    const result: string[] = [];

    function backtrack(index: number, path: string): void {
        if (index === digits.length) {
            result.push(path);
            return;
        }
        for (const ch of map[digits[index]]) {
            backtrack(index + 1, path + ch);
        }
    }

    backtrack(0, '');
    return result;
}

export { letterCombinations };
