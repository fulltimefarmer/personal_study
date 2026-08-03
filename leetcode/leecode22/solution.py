"""
考点：字符串、动态规划、回溯
题目：Generate Parentheses（括号生成）
思路：回溯法，维护已使用的左右括号数，左括号数 < n 时可添加左括号，右括号数 < 左括号数时可添加右括号
时间复杂度：O(4^n / sqrt(n))，这是第 n 个卡特兰数的渐近
空间复杂度：O(n)，递归栈深度
"""
from typing import List

def generateParenthesis(n: int) -> List[str]:
    result: list[str] = []

    # 回溯函数：path 是当前构建的括号字符串，open_count 和 close_count 是已使用的括号数量
    def backtrack(path: str, open_count: int, close_count: int) -> None:
        # 递归终止：当字符串长度达到 2*n 时，所有括号都已放置完毕
        if len(path) == 2 * n:
            result.append(path)
            return

        # 剪枝条件 1：左括号数量未达到 n 时，可以添加左括号
        if open_count < n:
            backtrack(path + "(", open_count + 1, close_count)

        # 剪枝条件 2：右括号数量必须小于左括号数量时才能添加右括号
        # 这保证了括号的有效性：任何前缀中右括号数不超过左括号数
        if close_count < open_count:
            backtrack(path + ")", open_count, close_count + 1)

    backtrack("", 0, 0)
    return result

if __name__ == "__main__":
    expected_3 = ["((()))", "(()())", "(())()", "()(())", "()()()"]
    assert sorted(generateParenthesis(3)) == sorted(expected_3)

    assert generateParenthesis(1) == ["()"]

    assert len(generateParenthesis(4)) == 14  # 卡特兰数 C(4) = 14
    print("全部通过 ✓")
