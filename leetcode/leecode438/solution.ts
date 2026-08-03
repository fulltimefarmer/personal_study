/**
 * 考点：哈希表、字符串、滑动窗口
 * 题目：Find All Anagrams in a String（找到字符串中所有字母异位词）
 * 题目描述：在 s 中找出所有 p 的字母异位词的起始索引
 * 思路：固定大小滑动窗口 + 计数数组。维护两个 26 长数组分别统计 p 和窗口。
 *       滑动比较，相等则记录起始索引。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function findAnagrams(s: string, p: string): number[] {
    const result: number[] = [];
    if (p.length > s.length) return result;

    const target = new Array(26).fill(0);
    const window = new Array(26).fill(0);
    const base = 'a'.charCodeAt(0);

    for (let i = 0; i < p.length; i++) {
        target[p.charCodeAt(i) - base]++;
        window[s.charCodeAt(i) - base]++;
    }

    const matches = (): boolean => {
        for (let i = 0; i < 26; i++) {
            if (target[i] !== window[i]) return false;
        }
        return true;
    };

    if (matches()) result.push(0);

    for (let i = p.length; i < s.length; i++) {
        window[s.charCodeAt(i) - base]++;
        window[s.charCodeAt(i - p.length) - base]--;
        if (matches()) result.push(i - p.length + 1);
    }

    return result;
}

export { findAnagrams };
