/**
 * 考点：String, Trie
 * 题目：Longest Common Prefix（最长公共前缀）
 * 题目描述：编写函数查找字符串数组中的最长公共前缀，如果不存在返回空字符串。
 * 示例：strs = ["flower","flow","flight"] => "fl"
 * 思路：以第一个字符串为基准，逐个与其余字符串比较，不断缩短前缀
 * 时间复杂度：O(S)，S 为所有字符串字符总数
 * 空间复杂度：O(1)
 */
function longestCommonPrefix(strs: string[]): string {
    if (strs.length === 0) return "";

    let prefix = strs[0];

    for (let i = 1; i < strs.length; i++) {
        while (!strs[i].startsWith(prefix)) {
            prefix = prefix.substring(0, prefix.length - 1);
            if (prefix === "") return "";
        }
    }

    return prefix;
}
export { longestCommonPrefix };
