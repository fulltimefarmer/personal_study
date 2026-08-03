/**
 * 考点：哈希表、字符串、排序
 * 题目：Valid Anagram（有效的字母异位词）
 * 题目描述：判断 t 是否是 s 的字母异位词（每个字符出现次数相同）。s="anagram",t="nagaram" 输出 true
 * 思路：26 位计数数组，s 的字符 +1，t 的字符 -1，最后检查是否全为 0。
 * 进阶（Unicode）：用 Map 代替数组。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function isAnagram(s: string, t: string): boolean {
    if (s.length !== t.length) return false;

    const count: number[] = new Array(26).fill(0);

    for (let i = 0; i < s.length; i++) {
        count[s.charCodeAt(i) - 97]++;
        count[t.charCodeAt(i) - 97]--;
    }

    for (const c of count) {
        if (c !== 0) return false;
    }

    return true;
}
export { isAnagram };
