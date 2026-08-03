"""
考点: Bit Manipulation, Array, Backtracking
题目: Subsets（子集）
题目描述: 给定互不相同的整数数组 nums，返回所有可能子集（幂集）。
示例: nums = [1,2,3] -> [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
思路: 回溯。对每个元素选或不选，递归树上的每个节点都是一个子集。
      也可用位运算枚举所有 mask。
时间复杂度: O(n * 2^n)
空间复杂度: O(n)
"""


def subsets(nums: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    path: list[int] = []

    def backtrack(index: int) -> None:
        # 关键: 每个递归节点都是一个合法子集，先加入结果
        # 这不同于组合问题（只在 leaf 收集），这里每个 node 都收集
        result.append(path[:])

        # 从 index 开始选择下一个加入的元素
        for i in range(index, len(nums)):
            path.append(nums[i])  # 选择当前元素
            backtrack(i + 1)      # 递归处理剩余元素
            path.pop()            # 回溯: 撤销选择

    backtrack(0)
    return result


if __name__ == "__main__":
    expected = [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    # 排序每组子集和结果以进行无序比较
    actual = sorted([sorted(sub) for sub in subsets([1, 2, 3])])
    expected_sorted = sorted([sorted(sub) for sub in expected])
    assert actual == expected_sorted

    assert subsets([]) == [[]]
    assert len(subsets([1, 2, 3, 4])) == 16  # 2^4 个子集
