/**
 * 考点：String, Dynamic Programming, Two Pointers
 * 题目：Longest Palindromic Substring（最长回文子串）
 * 题目描述：给定字符串 s，找到 s 中最长的回文子串。
 * 示例：s = "babad" => "bab" 或 "aba"
 * 思路：中心扩展法，对每个位置分别以单字符和双字符为中心向外扩展
 * 时间复杂度：O(n^2)
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
                maxLen = len;
                start = left;
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
