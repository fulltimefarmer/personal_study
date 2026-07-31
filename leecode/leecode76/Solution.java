/**
 * 考点：Hash Table、Sliding Window、Two Pointers
 * 题目：Minimum Window Substring
 * 题目描述：给你一个字符串 s、一个字符串 t，返回 s 中涵盖 t 所有字符的最小子串。
 *          如果不存在符合条件的子串，则返回空字符串 ""。
 *          注意：对于 t 中重复字符，我们寻找的子串中该字符数量必须不少于 t 中该字符数量。
 *          如果 s 中存在这样的子串，我们保证它是唯一的答案。
 *          示例：输入 s = "ADOBECODEBANC"，t = "ABC"，输出 "BANC"。
 * 思路：第一步：使用长度为 128 的整型数组 need 作为字符频次表，统计 t 中各字符需求量；
 *              missing 记录尚未满足的字符种类数（某一字符首次出现或频次从正变 0 时更新）。
 *       第二步：初始化 left = 0、start = 0、minLen = Integer.MAX_VALUE。
 *       第三步：右指针 right 从 0 到 s.length() - 1 扩展窗口：
 *              - need[ch]--，若减后恰好为 0，则 missing--。
 *       第四步：当 missing == 0 时窗口已满足条件，尝试收缩左边界：
 *              - 若窗口更短，更新 minLen 与 start。
 *              - lc = s.charAt(left)；若 need[lc] == 0，移出后不再满足，missing++；
 *                然后 need[lc]++，left++。
 *       第五步：遍历结束后，若 minLen 仍为 Integer.MAX_VALUE 返回空串，否则返回对应子串。
 * 算法：滑动窗口 + 哈希表（字符频次数组）。
 * 时间复杂度：O(|s| + |t|)
 * 空间复杂度：O(|Σ|)，字符集大小，通常视为 O(1)
 */
public class Solution {
    public String minWindow(String s, String t) {
        int[] need = new int[128];
        int missing = 0;
        for (char ch : t.toCharArray()) {
            if (need[ch] == 0) missing++;
            need[ch]++;
        }
        int left = 0, start = 0, minLen = Integer.MAX_VALUE;
        for (int right = 0; right < s.length(); right++) {
            char ch = s.charAt(right);
            need[ch]--;
            if (need[ch] == 0) missing--;
            while (missing == 0) {
                if (right - left + 1 < minLen) {
                    minLen = right - left + 1;
                    start = left;
                }
                char lc = s.charAt(left);
                if (need[lc] == 0) missing++;
                need[lc]++;
                left++;
            }
        }
        return minLen == Integer.MAX_VALUE ? "" : s.substring(start, start + minLen);
    }
}
