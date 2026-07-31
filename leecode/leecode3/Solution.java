/**
 * 考点：Sliding Window、Hash Table
 * 题目：Longest Substring Without Repeating Characters
 * 题目描述：
 *   给定一个字符串 s，请你找出其中不含有重复字符的最长子串的长度。
 *   示例 1：输入 s = "abcabcbb"，输出 3。解释：因为无重复字符的最长子串是 "abc"，所以其长度为 3。
 *   示例 2：输入 s = "bbbbb"，输出 1。解释：因为无重复字符的最长子串是 "b"，所以其长度为 1。
 *   示例 3：输入 s = "pwwkew"，输出 3。解释：因为无重复字符的最长子串是 "wke"，所以其长度为 3。
 *   注意：答案必须是子串的长度，"pwke" 是一个子序列，不是子串。
 *   提示：0 <= s.length <= 5 * 10^4，s 由英文字母、数字、符号和空格组成。
 * 思路：
 *   1. 初始化一个空集合 set，用于记录当前窗口内出现过的字符。
 *   2. 定义 left 指针指向窗口左边界，right 指针从左到右扩展窗口右边界。
 *   3. 右指针每移动到一个新字符 s.charAt(right)：
 *      a) 若该字符已在 set 中，说明出现重复，移动左指针，把 s.charAt(left) 从 set 中删除，left 右移，直到 s.charAt(right) 不再重复。
 *      b) 将 s.charAt(right) 加入 set。
 *      c) 用窗口长度 right - left + 1 更新 maxLen。
 *   4. 遍历结束后 maxLen 即为无重复字符的最长子串长度。
 * 数据结构：哈希集合（Hash Set）—— 基于哈希函数实现元素唯一性存储，平均 O(1) 查询/插入/删除。
 * 时间复杂度：O(n)
 * 空间复杂度：O(min(m, n))，其中 m 为字符集大小，n 为字符串长度
 */
class Solution {
    public int lengthOfLongestSubstring(String s) {
        java.util.Set<Character> set = new java.util.HashSet<>();
        int left = 0;
        int maxLen = 0;
        for (int right = 0; right < s.length(); right++) {
            while (set.contains(s.charAt(right))) {
                set.remove(s.charAt(left));
                left++;
            }
            set.add(s.charAt(right));
            maxLen = Math.max(maxLen, right - left + 1);
        }
        return maxLen;
    }
}
