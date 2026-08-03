"""
考点: Backtracking
题目: Combinations（组合）
题目描述: 给定 n 和 k，返回 [1, n] 中所有 k 个数的组合。
示例: n = 4, k = 2 -> [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
思路: 回溯。从 start 开始选数，避免重复。path 长度等于 k 时加入结果。
      剪枝优化: 剩余数字不足时提前终止。
时间复杂度: O(C(n, k) * k)
空间复杂度: O(k)
"""


def combine(n: int, k: int) -> list[list[int]]:
    result: list[list[int]] = []
    path: list[int] = []

    def backtrack(start: int) -> None:
        # 终止条件: path 中已选够 k 个数字
        if len(path) == k:
            # path[:] 创建 path 的浅拷贝，因为 path 在回溯过程中会被修改
            # 也可以用 path.copy() 或 list(path)
            result.append(path[:])
            return

        # 剪枝优化: 剩余可选数字数量需足够填满 path
        # 剩余可选数量 = n - i + 1，还需选 = k - len(path)
        # 循环上限 = n - (k - len(path)) + 1
        # Python 的 range(start, stop) 不包含 stop，所以 +1 已在 range 中隐含处理
        upper = n - (k - len(path)) + 1
        for i in range(start, upper + 1):  # 加 1 确保包含 upper
            path.append(i)       # 做选择: 将 i 加入当前路径
            backtrack(i + 1)     # 递归: 从 i+1 开始避免重复选择
            path.pop()           # 撤销选择: 回溯的核心操作

    backtrack(1)
    return result


if __name__ == "__main__":
    assert combine(4, 2) == [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
    assert combine(1, 1) == [[1]]
    # 验证 C(5,3) = 10 个组合
    assert len(combine(5, 3)) == 10
