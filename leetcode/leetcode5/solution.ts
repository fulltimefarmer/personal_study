/**
 * 考点：String, Dynamic Programming
 * 题目：Longest Palindromic Substring（最长回文子串）
 * 题目描述：找到字符串中的最长回文子串。如 "babad" → "bab" 或 "aba"
 * 思路：中心扩展法。遍历每个位置，以该位置为中心（奇数）或以两个位置之间为中心（偶数）向两侧扩展。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(1)
 */
function longestPalindrome(s: string): string {
    if (s.length < 2) return s;

    let start = 0;
    let maxLen = 1;

    function expandAroundCenter(left: number, right: number): void {
        while (left >= 0 && right < s.length && s[left] === s[right]) {
            const len = right - left + 1;
            if (len > maxLen) {
                start = left;
                maxLen = len;
            }
            left--;
            right++;
        }
    }

    for (let i = 0; i < s.length; i++) {
        expandAroundCenter(i, i);
        expandAroundCenter(i, i + 1);
    }

    return s.substring(start, start + maxLen);
}

export { longestPalindrome };
