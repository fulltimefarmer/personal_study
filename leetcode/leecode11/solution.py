"""
考点：数组、双指针、贪心
题目：Container With Most Water（盛最多水的容器）
思路：双指针从两端向中间收缩，每次移动较短的边（因为移动较长边不会增加面积），更新最大面积
时间复杂度：O(n)
空间复杂度：O(1)
"""
from typing import List

def maxArea(height: List[int]) -> int:
    left, right = 0, len(height) - 1  # 双指针：左指针从 0 开始，右指针从末尾开始
    max_water = 0  # 记录最大水量（面积）

    # 当左右指针未相遇时持续计算
    while left < right:
        # 当前容器的水量 = 较短挡板的高度 × 两挡板之间的距离
        h = min(height[left], height[right])  # 取较短的挡板（短板效应）
        area = h * (right - left)  # 宽度 = 索引差
        max_water = max(max_water, area)  # 更新最大值

        # 贪心策略：移动较短的一边
        # 因为移动较长边后，宽度减小且高度不可能超过当前较短边，面积必然更小
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1

    return max_water

if __name__ == "__main__":
    assert maxArea([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert maxArea([1, 1]) == 1
    assert maxArea([4, 3, 2, 1, 4]) == 16
    assert maxArea([1, 2, 1]) == 2
    print("全部通过 ✓")
