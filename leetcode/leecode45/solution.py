"""
考点：贪心、数组、动态规划
题目：Jump Game II（跳跃游戏 II）
思路：贪心算法，维护当前步数能到达的边界和下一步能到达的最远距离，到达边界时跳跃次数+1并更新边界
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def jump(nums: List[int]) -> int:
    # 只有一个元素或空数组，不需要跳跃
    if len(nums) <= 1:
        return 0

    jumps = 0  # 跳跃次数
    current_end = 0  # 当前跳跃步数下能到达的最远边界
    farthest = 0  # 在当前步数能到达的范围内，再跳一步能到达的最远位置

    # 遍历到 n-2 即可，因为不需要从最后一个位置起跳
    for i in range(len(nums) - 1):
        # 更新下一步能到达的最远距离
        # i + nums[i]：从当前位置 i 起跳能到达的最远位置
        farthest = max(farthest, i + nums[i])

        # 当到达当前步数能走到的最远边界时
        if i == current_end:
            jumps += 1  # 需要进行一次跳跃
            current_end = farthest  # 更新下一轮能到达的最远边界

            # 提前退出优化：如果当前边界已经覆盖了目标位置
            if current_end >= len(nums) - 1:
                break

    return jumps

if __name__ == "__main__":
    assert jump([2, 3, 1, 1, 4]) == 2
    assert jump([2, 3, 0, 1, 4]) == 2
    assert jump([0]) == 0
    assert jump([1, 2]) == 1
    print("全部通过 ✓")
