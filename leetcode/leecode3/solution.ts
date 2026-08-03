/**
 * 考点：Hash Table, String, Sliding Window
 * 题目：Longest Substring Without Repeating Characters（无重复字符的最长子串）
 * 题目描述：给定字符串 s，找出不含有重复字符的最长子串的长度。
 * 示例：s = "abcabcbb" => 3（"abc"）
 * 思路：滑动窗口 + 哈希表，维护左右指针和字符最近出现位置
 * 时间复杂度：O(n)
 * 空间复杂度：O(min(n, 字符集大小))
 */
function lengthOfLongestSubstring(s: string): number {
    const map = new Map<string, number>();
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {
        const char = s[right];
        if (map.has(char) && map.get(char)! >= left) {
            left = map.get(char)! + 1;
        }
        map.set(char, right);
        maxLen = Math.max(maxLen, right - left + 1);
    }

    return maxLen;
}
export { lengthOfLongestSubstring };
