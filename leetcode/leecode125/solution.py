"""
考点：Two Pointers, String
题目：Valid Palindrome（验证回文串）
题目描述：忽略大小写和非字母数字字符，判断字符串是否为回文串。
示例 1："A man, a plan, a canal: Panama"，输出 true
示例 2："race a car"，输出 false
示例 3：" "，输出 true（空字符串是回文串）
思路：双指针，跳过非字母数字字符，比较小写字符。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def isPalindrome(s: str) -> bool:
    left: int = 0
    right: int = len(s) - 1

    while left < right:
        # 左指针跳过非字母数字字符
        # str.isalnum() 判断字符是否为字母或数字（Python 内置方法）
        while left < right and not s[left].isalnum():
            left += 1
        # 右指针跳过非字母数字字符
        while left < right and not s[right].isalnum():
            right -= 1
        # 比较时都转为小写（str.lower()），忽略大小写
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1

    return True


if __name__ == "__main__":
    assert isPalindrome("A man, a plan, a canal: Panama") is True
    assert isPalindrome("race a car") is False
    assert isPalindrome(" ") is True
    assert isPalindrome("0P") is False
