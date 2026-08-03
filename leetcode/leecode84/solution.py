"""
考点: Stack, Array, Monotonic Stack
题目: Largest Rectangle in Histogram（柱状图中最大的矩形）
题目描述: 给定柱状图的高度数组 heights，求能勾勒出的最大矩形面积。
示例: heights = [2,1,5,6,2,3] -> 10
思路: 单调递增栈。对每个柱子找左右第一个比它矮的柱子作为边界，计算以它为高的矩形面积。
      末尾加哨兵 0 确保所有元素被处理。
时间复杂度: O(n)
空间复杂度: O(n)
"""


def largestRectangleArea(heights: list[int]) -> int:
    # 单调递增栈: 存索引，对应高度单调递增
    stack: list[int] = []
    max_area = 0
    heights.append(0)  # 哨兵: 确保最后所有元素都会出栈

    for i, h in enumerate(heights):
        # 当遇到比栈顶矮的柱子时，栈顶柱子找到了右边界，可以计算面积
        # 栈非空且当前高度 < 栈顶指向的高度
        while stack and h < heights[stack[-1]]:
            # 栈顶索引对应的柱子高度
            height = heights[stack.pop()]
            # 宽度: 如果栈为空，说明该柱子左侧没有更矮的，宽度为 i
            # 否则宽度为 i - 新栈顶索引 - 1（当前元素和新栈顶之间的柱子数）
            width = i if not stack else i - stack[-1] - 1
            area = height * width
            # walrus operator := 在表达式中同时赋值和比较 (Python 3.8+)
            if area > max_area:
                max_area = area
        stack.append(i)  # 当前索引入栈

    heights.pop()  # 恢复原数组（移除哨兵）
    return max_area


if __name__ == "__main__":
    assert largestRectangleArea([2, 1, 5, 6, 2, 3]) == 10
    assert largestRectangleArea([2, 4]) == 4
    assert largestRectangleArea([1]) == 1
    assert largestRectangleArea([0]) == 0
