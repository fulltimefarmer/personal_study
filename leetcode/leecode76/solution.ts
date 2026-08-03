/**
 * 考点：Hash Table, String, Sliding Window
 * 题目：Minimum Window Substring（最小覆盖子串）
 * 题目描述：给定字符串 s 和 t，返回 s 中涵盖 t 所有字符的最小子串。不存在则返回 ""。
 * 示例：s = "ADOBECODEBANC", t = "ABC" → "BANC"
 * 思路：滑动窗口 + 哈希表。右指针扩展窗口，满足条件后左指针收缩，
 *       用 need map 记录字符需求，valid 计数已满足的字符种类。
 * 时间复杂度：O(n)
 * 空间复杂度：O(|Σ|)
 */
function minWindow(s: string, t: string): string {
    const need = new Map<string, number>();
    for (const char of t) {
        need.set(char, (need.get(char) || 0) + 1);
    }

    const window = new Map<string, number>();
    let left = 0;
    let right = 0;
    let valid = 0;
    let start = 0;
    let minLen = Infinity;

    while (right < s.length) {
        const c = s[right];
        right++;

        if (need.has(c)) {
            window.set(c, (window.get(c) || 0) + 1);
            if (window.get(c) === need.get(c)) {
                valid++;
            }
        }

        while (valid === need.size) {
            if (right - left < minLen) {
                start = left;
                minLen = right - left;
            }

            const d = s[left];
            left++;

            if (need.has(d)) {
                if (window.get(d) === need.get(d)) {
                    valid--;
                }
                window.set(d, window.get(d)! - 1);
            }
        }
    }

    return minLen === Infinity ? "" : s.substring(start, start + minLen);
}

export { minWindow };
