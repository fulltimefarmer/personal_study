"""
考点: Greedy, Array, Dynamic Programming
题目: Jump Game（跳跃游戏）
题目描述: 给定非负整数数组 nums，最初位于第一个下标，每个元素代表可跳跃的最大长度，判断是否能到达最后一个下标。
示例: nums = [2,3,1,1,4] -> true
示例: nums = [3,2,1,0,4] -> false
思路: 贪心算法。维护 maxReach 表示当前能到达的最远距离，遍历时若 i > maxReach 则不可达，
      不断更新 maxReach，一旦 >= n-1 即可返回 true。
时间复杂度: O(n)
空间复杂度: O(1)
"""


def canJump(nums: list[int]) -> bool:
    max_reach = 0
    n = len(nums)

    # enumerate() 同时获取索引 i 和值 num，是 Python 遍历的可读写法
    for i, jump in enumerate(nums):
        # 当前位置超过了能到达的最远距离 -> 永远到不了这里
        if i > max_reach:
            return False
        # 更新最远可达距离: max(之前最远, 当前位置 + 可跳距离)
        max_reach = max(max_reach, i + jump)
        # 提前终止: 如果能达到或超过最后一个位置
        if max_reach >= n - 1:
            return True

    return True


if __name__ == "__main__":
    assert canJump([2, 3, 1, 1, 4]) is True
    assert canJump([3, 2, 1, 0, 4]) is False
    assert canJump([0]) is True  # 只有一个元素，已在终点
