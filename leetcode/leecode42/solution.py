"""
考点：栈、数组、双指针、动态规划、单调栈
题目：Trapping Rain Water（接雨水）
思路：双指针法，维护左右最大高度，每次处理较低的一侧，当前位置的积水量由该侧的最大高度减去当前高度
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def trap(height: List[int]) -> int:
    if not height:
        return 0

    left, right = 0, len(height) - 1  # 左右双指针
    left_max, right_max = 0, 0  # 左右两侧当前遇到的最大高度
    water = 0  # 累计接水量

    while left < right:
        # 总是处理高度较低的一侧
        # 因为每个位置的积水量由较矮的挡板决定（木桶效应）
        if height[left] < height[right]:
            # 处理左侧
            if height[left] >= left_max:
                left_max = height[left]  # 更新左侧最大高度（此位置不能积水）
            else:
                water += left_max - height[left]  # 此处可以积累 left_max - height[left] 的水
            left += 1  # 左指针右移
        else:
            # 处理右侧
            if height[right] >= right_max:
                right_max = height[right]  # 更新右侧最大高度（此位置不能积水）
            else:
                water += right_max - height[right]  # 此处可以积累 right_max - height[right] 的水
            right -= 1  # 右指针左移

    return water

if __name__ == "__main__":
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap([4, 2, 0, 3, 2, 5]) == 9
    assert trap([]) == 0
    assert trap([1]) == 0
    print("全部通过 ✓")
