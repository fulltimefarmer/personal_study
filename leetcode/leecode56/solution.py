"""
考点: Array, Sorting
题目: Merge Intervals（合并区间）
题目描述: 给定区间数组 intervals，合并所有重叠区间，返回不重叠的区间数组。
示例: intervals = [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]]
示例: intervals = [[1,4],[4,5]] -> [[1,5]]
思路: 按起始位置排序后遍历，若当前区间与结果末尾区间重叠则扩展右边界，否则加入新区间。
时间复杂度: O(n log n)
空间复杂度: O(n)
"""


def merge(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []

    # key=lambda x: x[0] 表示按区间的起始位置排序
    # lambda 是 Python 的匿名函数，x[0] 取每个区间的第一个元素（起始值）
    intervals.sort(key=lambda x: x[0])

    # 初始化结果列表，放入第一个区间作为基准
    result = [intervals[0]]

    for i in range(1, len(intervals)):
        # result[-1] 是 Python 取列表最后一个元素的简洁写法（-1 表示倒数第一个）
        # Python 列表是引用类型，直接修改 last[1] 会影响 result 中的元素
        last = result[-1]
        current = intervals[i]

        # 判断重叠: 当前区间的起点 <= 上一个区间的终点
        if current[0] <= last[1]:
            # 合并: 扩展上一个区间的终点为两者终点的较大值
            last[1] = max(last[1], current[1])
        else:
            result.append(current)

    return result


if __name__ == "__main__":
    assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge([[1, 4], [0, 4]]) == [[0, 4]]  # 包含关系
