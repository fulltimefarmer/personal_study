/**
 * 考点：Hash Table、String
 * 题目：Group Anagrams
 * 题目描述：给你一个字符串数组 strs，请你将字母异位词组合在一起。
 *          字母异位词（Anagram）是由重新排列源单词的所有字母得到的一个新单词。
 *          可以按任意顺序返回结果列表。
 *          所有输入字符串都为小写字母。
 * 思路：第一步：创建一个哈希表 Map，用于存储“排序后的字符串”到“原字符串列表”的映射。
 *       第二步：遍历字符串数组 strs 中的每个单词 str。
 *       第三步：对当前单词的字符进行排序并拼接成字符串作为 key；
 *              互为字母异位词的单词排序后 key 相同，因此会被归入同一组。
 *       第四步：将原单词 str 加入 key 对应的列表中；若 key 不存在则先创建一个空列表。
 *       第五步：遍历结束后，返回哈希表中所有 value 列表组成的数组。
 * 算法：哈希表 —— key 为排序后的字符串，value 为原字符串数组。
 * 时间复杂度：O(n * k log k)，其中 n 是字符串个数，k 是字符串最大长度
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
