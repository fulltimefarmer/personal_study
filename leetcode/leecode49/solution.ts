/**
 * 考点：Array, Hash Table, String, Sorting
 * 题目：Group Anagrams（字母异位词分组）
 * 题目描述：将字母异位词（由相同字母重排列组成）组合在一起返回。
 * 示例：strs = ["eat", "tea", "tan", "ate", "nat", "bat"] => [["bat"],["nat","tan"],["ate","eat","tea"]]
 * 思路：对每个字符串排序作为键，用哈希表分组
 * 时间复杂度：O(n * k log k)
 * 空间复杂度：O(n * k)
 */
function groupAnagrams(strs: string[]): string[][] {
    const map = new Map<string, string[]>();

    for (const str of strs) {
        const key = str.split("").sort().join("");
        if (!map.has(key)) {
            map.set(key, []);
        }
        map.get(key)!.push(str);
    }

    return Array.from(map.values());
}
export { groupAnagrams };
