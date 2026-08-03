"""
考点：Array, Dynamic Programming
题目：Pascal's Triangle（杨辉三角）
题目描述：生成杨辉三角的前 numRows 行。每个数是它左上方和右上方的数的和。
示例 1：numRows = 5，输出 [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]
示例 2：numRows = 1，输出 [[1]]
思路：逐行构建，首尾元素为 1，中间元素为上一行相邻两元素之和。
时间复杂度：O(numRows^2)
空间复杂度：O(1)（不计返回值）
"""


def generate(numRows: int) -> list[list[int]]:
    result: list[list[int]] = []

    for i in range(numRows):
        # 每行开头和结尾都是 1，先初始化整行为 1
        row: list[int] = [1] * (i + 1)  # 第 i 行有 i+1 个元素
        # 中间元素（索引 1 到 i-1）由上一行相邻两元素相加得到
        for j in range(1, i):
            row[j] = result[i - 1][j - 1] + result[i - 1][j]
        result.append(row)

    return result


if __name__ == "__main__":
    assert generate(5) == [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]
    assert generate(1) == [[1]]
    assert generate(0) == []
