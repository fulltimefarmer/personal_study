/**
 * 考点：Hash Table, String, Sliding Window
 * 题目：Longest Substring Without Repeating Characters（无重复字符的最长子串）
 * 题目描述：找出字符串中不含有重复字符的最长子串的长度。如 "abcabcbb" → 3 ("abc")
 * 思路：滑动窗口 + 哈希表记录字符最后出现位置。遇到重复字符时左指针跳到重复字符的下一个位置。
 * 时间复杂度：O(n)
 * 空间复杂度：O(min(m, n))
 */
function lengthOfLongestSubstring(s: string): number {
    const map = new Map<string, number>();
    let left = 0;
    let maxLen = 0;

    for (let right = 0; right < s.length; right++) {
        const ch = s[right];
        if (map.has(ch) && map.get(ch)! >= left) {
            left = map.get(ch)! + 1;
        }
        map.set(ch, right);
        maxLen = Math.max(maxLen, right - left + 1);
    }

    return maxLen;
}

export { lengthOfLongestSubstring };
