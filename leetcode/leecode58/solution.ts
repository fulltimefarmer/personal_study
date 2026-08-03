/**
 * 考点：String
 * 题目：Length of Last Word（最后一个单词的长度）
 * 题目描述：给定由单词和空格组成的字符串 s，返回最后一个单词的长度。
 * 示例：s = "Hello World" → 5
 * 示例：s = "   fly me   to   the moon  " → 4
 * 思路：从字符串末尾向前遍历，跳过末尾空格后，计数第一个非空格连续字符的长度。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function lengthOfLastWord(s: string): number {
    let end = s.length - 1;

    while (end >= 0 && s[end] === ' ') {
        end--;
    }

    let length = 0;
    while (end >= 0 && s[end] !== ' ') {
        length++;
        end--;
    }

    return length;
}

export { lengthOfLastWord };
