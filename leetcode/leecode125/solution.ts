/**
 * 考点：Two Pointers, String
 * 题目：Valid Palindrome（验证回文串）
 * 题目描述：忽略大小写和非字母数字字符，判断字符串是否为回文串。
 * 示例 1："A man, a plan, a canal: Panama"，输出 true
 * 示例 2："race a car"，输出 false
 * 示例 3：" "，输出 true（空字符串是回文串）
 * 思路：双指针，跳过非字母数字字符，比较小写字符。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function isPalindrome(s: string): boolean {
    let left = 0;
    let right = s.length - 1;

    while (left < right) {
        while (left < right && !isAlphanumeric(s[left])) left++;
        while (left < right && !isAlphanumeric(s[right])) right--;

        if (s[left].toLowerCase() !== s[right].toLowerCase()) {
            return false;
        }
        left++;
        right--;
    }

    return true;
}

function isAlphanumeric(ch: string): boolean {
    const code = ch.charCodeAt(0);
    return (
        (code >= 48 && code <= 57) ||
        (code >= 65 && code <= 90) ||
        (code >= 97 && code <= 122)
    );
}

export { isPalindrome };
