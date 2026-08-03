"""
考点：数组、回溯
题目：Combination Sum（组合总和）
思路：回溯法，从 start 索引开始遍历 candidates，每个元素可以使用多次，通过 remaining 追踪剩余目标值
时间复杂度：O(N^(T/M))，T 是 target，M 是最小候选值
空间复杂度：O(T/M)，递归栈深度
"""
from typing import List

def combinationSum(candidates: List[int], target: int) -> List[List[int]]:
    result: list[list[int]] = []

    def backtrack(start: int, path: list[int], remaining: int) -> None:
        """回溯函数"""
        # 剪枝：剩余值小于 0 说明当前路径不可能得到答案
        if remaining < 0:
            return
        # 找到一组解：剩余值恰好为 0
        if remaining == 0:
            # path[:] 或 list(path) 创建 path 的浅拷贝，避免后续修改影响结果
            result.append(path[:])
            return

        # 从 start 开始遍历，而非每次都从 0 开始
        # 这样做避免生成重复组合（如 [2,3] 和 [3,2] 视为同一组合）
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            # 关键：递归时 start 参数仍是 i（不是 i+1）
            # 因为题目允许同一个数字被重复使用多次
            backtrack(i, path, remaining - candidates[i])
            path.pop()  # 回溯：撤销选择，恢复状态

    backtrack(0, [], target)
    return result

if __name__ == "__main__":
    actual = combinationSum([2, 3, 6, 7], 7)
    expected = [[2, 2, 3], [7]]
    assert sorted([sorted(x) for x in actual]) == sorted([sorted(x) for x in expected])

    actual = combinationSum([2, 3, 5], 8)
    expected = [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    assert sorted([sorted(x) for x in actual]) == sorted([sorted(x) for x in expected])

    assert combinationSum([2], 1) == []
    print("全部通过 ✓")
