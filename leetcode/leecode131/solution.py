"""
考点：String, Dynamic Programming, Backtracking
题目：Palindrome Partitioning（分割回文串）
题目描述：将字符串分割，使每个子串都是回文串，返回所有可能的分割方案。
示例 1：s = "aab"，输出 [["a","a","b"],["aa","b"]]
示例 2：s = "a"，输出 [["a"]]
思路：回溯 + 回文判断。枚举切割位置，当前子串是回文则递归处理剩余部分。
时间复杂度：O(n * 2^n)
空间复杂度：O(n)
"""


def partition(s: str) -> list[list[str]]:
    result: list[list[str]] = []
    path: list[str] = []

    def is_palindrome(left: int, right: int) -> bool:
        """双指针判断 s[left..right] 是否为回文串"""
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    def backtrack(start: int) -> None:
        """从 start 位置开始尝试切割"""
        # 递归终止条件：start 到达字符串末尾，说明完成一次分割
        if start == len(s):
            # path[:] 或 list(path) 创建 path 的副本，防止后续回溯修改
            result.append(path[:])
            return

        # 枚举切割结束位置 end
        for end in range(start, len(s)):
            # 如果 s[start..end] 是回文串，则切割
            if is_palindrome(start, end):
                # Python 切片 s[start:end+1] 取子串（左闭右开，所以 end+1）
                path.append(s[start:end + 1])
                # 递归处理剩余部分（end+1 开始）
                backtrack(end + 1)
                # 回溯：撤销本次切割，尝试下一个切割位置
                path.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    assert sorted(partition("aab")) == sorted([["a", "a", "b"], ["aa", "b"]])
    assert partition("a") == [["a"]]
    assert partition("") == [[]]
