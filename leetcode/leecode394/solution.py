"""
考点：栈、递归、字符串
题目：Decode String（字符串解码）—— LeetCode 394
题目描述：编码规则 k[encoded_string]，解码还原字符串
思路：双栈法。数字栈存重复次数，字符串栈存前缀。
      遇 '[' 压栈保存状态，遇 ']' 弹出栈顶拼接重复字符串。
时间复杂度：O(S)，S 为解码后字符串长度
空间复杂度：O(S)
"""

def decodeString(s: str) -> str:
    # num_stack：存储遇到 '[' 之前的重复次数 k
    num_stack: list[int] = []
    # str_stack：存储遇到 '[' 之前已经构建好的字符串前缀
    str_stack: list[str] = []
    # current_str：当前正在构建的字符串
    current_str: str = ""
    # current_num：当前正在解析的数字
    current_num: int = 0

    for ch in s:
        if ch.isdigit():
            # 处理多位数：例如 "12[abc]"，需要累积 1 → 12
            # ord(ch) - ord('0') 将字符数字转为整数值
            current_num = current_num * 10 + int(ch)
        elif ch == "[":
            # 遇到 '['，将当前状态压栈，开始处理括号内的内容
            num_stack.append(current_num)
            str_stack.append(current_str)
            current_num = 0
            current_str = ""
        elif ch == "]":
            # 遇到 ']'，弹出栈顶状态，拼接重复字符串
            repeat = num_stack.pop()  # 弹出之前保存的重复次数
            prev_str = str_stack.pop()  # 弹出之前保存的前缀字符串
            # str * int 表示将字符串重复 int 次
            current_str = prev_str + current_str * repeat
        else:
            # 普通字母，追加到当前字符串
            current_str += ch

    return current_str


if __name__ == "__main__":
    assert decodeString("3[a]2[bc]") == "aaabcbc"
    assert decodeString("3[a2[c]]") == "accaccacc"
    assert decodeString("2[abc]3[cd]ef") == "abcabccdcdcdef"
    assert decodeString("abc3[cd]xyz") == "abccdcdcdxyz"
    assert decodeString("10[leetcode]") == "leetcode" * 10
    assert decodeString("2[a]") == "aa"
    print("所有断言通过！")
