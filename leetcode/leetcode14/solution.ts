/**
 * 考点：String, Trie
 * 题目：Longest Common Prefix（最长公共前缀）
 * 题目描述：找字符串数组的最长公共前缀。如 ["flower","flow","flight"] → "fl"
 * 思路：纵向扫描，以第一个字符串为基准，逐位比较其他字符串的对应字符。
 * 时间复杂度：O(n * m)
 * 空间复杂度：O(1)
 */
function longestCommonPrefix(strs: string[]): string {
    if (strs.length === 0) return '';

    for (let i = 0; i < strs[0].length; i++) {
        const ch = strs[0][i];
        for (let j = 1; j < strs.length; j++) {
            if (i >= strs[j].length || strs[j][i] !== ch) {
                return strs[0].substring(0, i);
            }
        }
    }
    return strs[0];
}

export { longestCommonPrefix };
