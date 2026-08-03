/**
 * 考点：哈希表、字符串、计数
 * 题目：Ransom Note（赎金信）
 * 题目描述：判断 ransomNote 能否由 magazine 中的字符构成（每个字符只能用一次）
 * 思路：用长度 26 的数组统计 magazine 字符频率，
 *       遍历 ransomNote 逐个扣减，出现负数即返回 false。
 * 时间复杂度：O(m + n)
 * 空间复杂度：O(1)
 */
function canConstruct(ransomNote: string, magazine: string): boolean {
    const count = new Array(26).fill(0);
    const base = 'a'.charCodeAt(0);

    for (const ch of magazine) {
        count[ch.charCodeAt(0) - base]++;
    }

    for (const ch of ransomNote) {
        const idx = ch.charCodeAt(0) - base;
        count[idx]--;
        if (count[idx] < 0) return false;
    }

    return true;
}

export { canConstruct };
