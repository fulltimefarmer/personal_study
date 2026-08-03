"""
考点：Array, Dynamic Programming
题目：Pascal's Triangle II（杨辉三角II）
题目描述：返回杨辉三角的第 rowIndex 行（0 索引）。
示例 1：rowIndex = 3，输出 [1,3,3,1]
示例 2：rowIndex = 0，输出 [1]
示例 3：rowIndex = 1，输出 [1,1]
思路：滚动数组，从后向前更新，空间 O(k)。
时间复杂度：O(rowIndex^2)
空间复杂度：O(rowIndex)
"""


def getRow(rowIndex: int) -> list[int]:
    # 初始化一行，全为 0，第一个元素设为 1
    row: list[int] = [0] * (rowIndex + 1)
    row[0] = 1

    for i in range(1, rowIndex + 1):
        # 从后向前更新，因为 row[j] 依赖 row[j-1]（上一轮的值）
        # 如果从前向后，row[j-1] 已经被当前轮覆盖，会出错
        for j in range(i, 0, -1):
            # row[j] 本身上一轮的值 + row[j-1] 上一轮的值（因为从右向左，row[j-1] 未更新）
            row[j] = row[j] + row[j - 1]

    return row


if __name__ == "__main__":
    assert getRow(3) == [1, 3, 3, 1]
    assert getRow(0) == [1]
    assert getRow(1) == [1, 1]
    assert getRow(4) == [1, 4, 6, 4, 1]
