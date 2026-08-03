"""
考点：哈希表、字符串、回溯
题目：Letter Combinations of a Phone Number（电话号码的字母组合）
思路：建立数字到字母的映射字典，使用回溯法逐位构建所有可能的字母组合
时间复杂度：O(3^m * 4^n)，m 是对应 3 个字母的数字个数，n 是 4 个字母的
空间复杂度：O(m + n)，递归栈深度
"""
from typing import List

def letterCombinations(digits: str) -> List[str]:
    if not digits:  # 空输入直接返回空列表
        return []

    # 数字到字母的映射表，和手机键盘一致
    # keys 2-6 有 3 个字母，7 和 9 有 4 个字母，8 有 3 个字母
    phone_map: dict[str, str] = {
        "2": "abc",
        "3": "def",
        "4": "ghi",
        "5": "jkl",
        "6": "mno",
        "7": "pqrs",
        "8": "tuv",
        "9": "wxyz",
    }

    result: list[str] = []

    # 回溯函数：index 表示当前处理到 digits 的第几个数字，path 是当前构建的字符串
    def backtrack(index: int, path: str) -> None:
        # 递归终止条件：所有数字都处理完毕
        if index == len(digits):
            result.append(path)  # 将构建好的组合加入结果
            return

        # 获取当前数字对应的所有字母，逐一尝试
        letters = phone_map[digits[index]]
        for letter in letters:
            # 递归处理下一个数字，path + letter 创建新的字符串（不修改原字符串）
            backtrack(index + 1, path + letter)

    backtrack(0, "")  # 从第 0 个数字开始，空字符串作为初始路径
    return result

if __name__ == "__main__":
    expected = ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]
    assert sorted(letterCombinations("23")) == sorted(expected)
    assert letterCombinations("") == []
    assert letterCombinations("2") == ["a", "b", "c"]
    print("全部通过 ✓")
