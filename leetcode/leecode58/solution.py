"""
考点: String
题目: Length of Last Word（最后一个单词的长度）
题目描述: 给定由单词和空格组成的字符串 s，返回最后一个单词的长度。
示例: s = "Hello World" -> 5
示例: s = "   fly me   to   the moon  " -> 4
思路: 从字符串末尾向前遍历，跳过末尾空格后，计数第一个非空格连续字符的长度。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def lengthOfLastWord(s: str) -> int:
    # end 指向最后一个字符的索引
    end = len(s) - 1

    # 第一步: 跳过末尾的所有空格
    while end >= 0 and s[end] == ' ':
        end -= 1

    # 第二步: 从末尾第一个非空格字符开始，计数直到遇到空格
    length = 0
    # Python 字符串支持索引访问 s[i]，负索引表示从末尾算起
    while end >= 0 and s[end] != ' ':
        length += 1
        end -= 1

    return length


if __name__ == "__main__":
    assert lengthOfLastWord("Hello World") == 5
    assert lengthOfLastWord("   fly me   to   the moon  ") == 4
    assert lengthOfLastWord("a") == 1
    assert lengthOfLastWord("a ") == 1
