/**
 * 考点：String, Two Pointers
 * 题目：Find the Index of the First Occurrence in a String（找出字符串中第一个匹配项的下标）
 * 题目描述：在 haystack 中找出 needle 的第一个匹配项的下标，不存在返回 -1。
 * 示例：haystack = "sadbutsad", needle = "sad" => 0
 * 思路：滑动窗口，遍历每个可能的起始位置，逐字符匹配
 * 时间复杂度：O(n * m)
 * 空间复杂度：O(1)
 */
function strStr(haystack: string, needle: string): number {
    const n = haystack.length;
    const m = needle.length;

    if (m === 0) return 0;

    for (let i = 0; i <= n - m; i++) {
        if (haystack.substring(i, i + m) === needle) {
            return i;
        }
    }

    return -1;
}
export { strStr };
