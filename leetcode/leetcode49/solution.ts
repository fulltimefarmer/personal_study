/**
 * 考点：Array, Hash Table, String, Sorting
 * 题目：Group Anagrams（字母异位词分组）
 * 题目描述：将字母异位词分组。如 ["eat","tea","tan","ate","nat","bat"] → [["bat"],["nat","tan"],["ate","eat","tea"]]
 * 思路：排序后字符串作为哈希表键分组。也可用26字母计数编码作为键优化。
 * 时间复杂度：O(n × k log k)
 * 空间复杂度：O(n × k)
 */
function groupAnagrams(strs: string[]): string[][] {
    const map = new Map<string, string[]>();

    for (const s of strs) {
        const key = s.split('').sort().join('');
        if (!map.has(key)) {
            map.set(key, []);
        }
        map.get(key)!.push(s);
    }

    return Array.from(map.values());
}

export { groupAnagrams };
