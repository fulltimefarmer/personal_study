"""
考点：贪心, 数组, 排序
题目：Minimum Number of Arrows to Burst Balloons（用最少数量的箭引爆气球）—— LeetCode 452
题目描述：有一些球形气球 points，points[i] = [x_start, x_end]。一支箭在 x 处射出可引爆满足 x_start <= x <= x_end 的气球。求引爆所有气球的最小弓箭数。
思路：贪心法。按气球结束位置排序，遍历时如果当前气球开始位置 > 当前箭的位置，需要新箭，更新箭的位置为当前气球结束位置。
时间复杂度：O(n log n)
空间复杂度：O(log n)
"""

def findMinArrowShots(points: list[list[int]]) -> int:
    if not points:
        return 0  # 没有气球，不需要箭

    # 按气球的结束位置 x_end 升序排序
    # 贪心策略：每支箭尽可能在气球的结束位置射出，覆盖最多气球
    points.sort(key=lambda x: x[1])

    arrows = 1  # 至少需要一支箭
    arrow_pos = points[0][1]  # 第一支箭射在第一个气球的结束位置

    for i in range(1, len(points)):
        # 如果当前气球的开始位置 > 当前箭的位置
        # 说明当前箭无法引爆这个气球，需要新的一支箭
        if points[i][0] > arrow_pos:
            arrows += 1
            arrow_pos = points[i][1]  # 新箭射在当前气球的结束位置

    return arrows


if __name__ == "__main__":
    assert findMinArrowShots([[10, 16], [2, 8], [1, 6], [7, 12]]) == 2
    assert findMinArrowShots([[1, 2], [3, 4], [5, 6], [7, 8]]) == 4
    assert findMinArrowShots([[1, 2], [2, 3], [3, 4], [4, 5]]) == 2
    assert findMinArrowShots([]) == 0
    assert findMinArrowShots([[1, 2]]) == 1
    # 重叠在边界的测试
    assert findMinArrowShots([[1, 2], [2, 3]]) == 1  # 在 x=2 射箭可以引爆两个
    assert findMinArrowShots([[1, 5], [2, 3], [4, 6]]) == 2
    print("所有断言通过！")
