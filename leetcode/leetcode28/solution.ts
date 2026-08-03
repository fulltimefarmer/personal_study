/**
 * 考点：Two Pointers, String, String Matching
 * 题目：Find the Index of the First Occurrence in a String（找出字符串中第一个匹配项的下标）
 * 题目描述：在haystack中找needle首次出现的位置。如 "sadbutsad", "sad" → 0
 * 思路：暴力匹配，每个起始位置检查子串。也可用KMP优化至O(n+m)。
 * 时间复杂度：O(n * m)
 * 空间复杂度：O(1)
 */
function strStr(haystack: string, needle: string): number {
    const n = haystack.length;
    const m = needle.length;
    if (m === 0) return 0;

    for (let i = 0; i <= n - m; i++) {
        let j = 0;
        while (j < m && haystack[i + j] === needle[j]) {
            j++;
        }
        if (j === m) return i;
    }
    return -1;
}

export { strStr };
