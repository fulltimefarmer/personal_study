"""
考点：数组、回溯
题目：Permutations（全排列）
思路：回溯法，使用 used 布尔数组标记已使用的元素，构建所有可能的排列组合
时间复杂度：O(n * n!)
空间复杂度：O(n)（递归栈 + used 数组）
"""
from typing import List

def permute(nums: List[int]) -> List[List[int]]:
    result: list[list[int]] = []
    n = len(nums)

    # used 数组：记录每个位置的元素是否已在当前排列中被使用
    # 这保证了每个元素在排列中只出现一次
    used: list[bool] = [False] * n

    def backtrack(path: list[int]) -> None:
        # 递归终止：当前路径长度等于数组长度，找到一个完整排列
        if len(path) == n:
            # path[:] 是切片操作，创建浅拷贝
            # 如果不拷贝，之后 path.pop() 会破坏已存储的结果
            result.append(path[:])
            return

        # 遍历所有未使用的元素
        for i in range(n):
            if used[i]:
                continue  # 跳过已使用的元素

            used[i] = True  # 标记为已使用
            path.append(nums[i])  # 将当前元素加入排列

            backtrack(path)  # 递归构建下一个位置

            path.pop()  # 回溯：移除最后一个元素
            used[i] = False  # 回溯：取消标记

    backtrack([])  # 空路径开始
    return result

if __name__ == "__main__":
    expected = [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    assert sorted(permute([1, 2, 3])) == sorted(expected)

    assert permute([0, 1]) == [[0, 1], [1, 0]]
    assert permute([1]) == [[1]]
    print("全部通过 ✓")
