/**
 * 考点：双指针、字符串
 * 题目：Valid Palindrome（验证回文串）
 * 题目描述：只考虑字母和数字字符，忽略大小写，判断字符串是否为回文串。
 *   示例：s = "A man, a plan, a canal: Panama" → true
 * 思路：双指针。左右指针向中间移动，跳过非字母数字字符，转为小写后比较。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function isPalindrome(s: string): boolean {
  let left = 0;
  let right = s.length - 1;

  while (left < right) {
    while (left < right && !isAlphanumeric(s[left])) {
      left++;
    }
    while (left < right && !isAlphanumeric(s[right])) {
      right--;
    }
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
    (code >= 48 && code <= 57) ||  // 0-9
    (code >= 65 && code <= 90) ||  // A-Z
    (code >= 97 && code <= 122)    // a-z
  );
}

export { isPalindrome };
