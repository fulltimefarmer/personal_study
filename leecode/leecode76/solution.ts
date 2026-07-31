/**
 * 考点：Hash Table、Sliding Window、Two Pointers
 * 题目：Minimum Window Substring
 * 题目描述：给你一个字符串 s、一个字符串 t，返回 s 中涵盖 t 所有字符的最小子串。
 *          如果不存在符合条件的子串，则返回空字符串 ""。
 *          注意：对于 t 中重复字符，我们寻找的子串中该字符数量必须不少于 t 中该字符数量。
 *          如果 s 中存在这样的子串，我们保证它是唯一的答案。
 *          示例：输入 s = "ADOBECODEBANC"，t = "ABC"，输出 "BANC"。
 * 思路：第一步：使用哈希表 need 统计 t 中每个字符的需求量；
 *              missing 记录尚未满足的字符种类数（某一字符需求量从正数减到 0 时，missing 减 1）。
 *       第二步：初始化 left = 0、start = 0、minLen = Infinity，表示当前窗口、最小窗口起点及长度。
 *       第三步：右指针 right 从 0 到 s.length - 1 遍历：
 *              - 若 s[right] 是 need 中的字符，将其需求量减 1；
 *                当该字符需求量恰好变为 0 时，missing 减 1。
 *       第四步：当 missing == 0 时，说明当前窗口已覆盖 t，尝试收缩左边界：
 *              - 若当前窗口长度更短，更新 minLen 与 start。
 *              - 将 s[left] 移出窗口；若该字符在 need 中且需求量已为 0，则移出后 missing 加 1，
 *                并将 need 中该字符需求量加 1。
 *              - left 右移。
 *       第五步：遍历结束后，若 minLen 仍为 Infinity 返回空串，否则返回 s.substring(start, start + minLen)。
 * 算法：滑动窗口 + 哈希表。
 * 时间复杂度：O(|s| + |t|)
 * 空间复杂度：O(|Σ|)，字符集大小，通常视为 O(1)
 */
function minWindow(s: string, t: string): string {
    const need = new Map<string, number>();
    for (const ch of t) {
        need.set(ch, (need.get(ch) || 0) + 1);
    }
    let missing = need.size;
    let left = 0, start = 0, minLen = Infinity;
    for (let right = 0; right < s.length; right++) {
        const ch = s[right];
        if (need.has(ch)) {
            need.set(ch, need.get(ch)! - 1);
            if (need.get(ch)! === 0) missing--;
        }
        while (missing === 0) {
            if (right - left + 1 < minLen) {
                minLen = right - left + 1;
                start = left;
            }
            const lc = s[left];
            if (need.has(lc)) {
                if (need.get(lc)! === 0) missing++;
                need.set(lc, need.get(lc)! + 1);
            }
            left++;
        }
    }
    return minLen === Infinity ? "" : s.substring(start, start + minLen);
}
