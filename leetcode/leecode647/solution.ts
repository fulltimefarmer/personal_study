/**
 * 考点：双指针, 字符串, 动态规划
 * 题目：Palindromic Substrings（回文子串）
 * 题目描述：给定字符串 s，统计所有回文子串的数量。
 * 示例：
 *   输入: "abc" → 输出: 3 ("a","b","c")
 *   输入: "aaa" → 输出: 6
 * 思路：中心扩展法。以每个位置为中心（奇数和偶数长度），向两边扩展，遇到回文就计数。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(1)
 */
function countSubstrings(s: string): number {
    const n = s.length;
    let count = 0;

    function expand(left: number, right: number): void {
        while (left >= 0 && right < n && s[left] === s[right]) {
            count++;
            left--;
            right++;
        }
    }

    for (let i = 0; i < n; i++) {
        expand(i, i);
        expand(i, i + 1);
    }

    return count;
}

export { countSubstrings };
