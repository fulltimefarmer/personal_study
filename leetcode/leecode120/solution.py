"""
考点：Array, Dynamic Programming
题目：Triangle（三角形最小路径和）
题目描述：给定三角形，找出自顶向下的最小路径和。每一步只能移动到下一行相邻结点（下标相同或 +1）。
示例：triangle = [[2],[3,4],[6,5,7],[4,1,8,3]]，输出 11（2+3+5+1）
思路：自底向上 DP，dp[j] = triangle[i][j] + min(dp[j], dp[j+1])，空间 O(n)。
时间复杂度：O(n^2)
空间复杂度：O(n)
"""


def minimumTotal(triangle: list[list[int]]) -> int:
    n: int = len(triangle)
    # 从最后一行开始初始化 dp 数组
    dp: list[int] = triangle[n - 1][:]  # [:] 浅拷贝，因为元素是 int

    # 自底向上，从倒数第二行开始往上计算
    for i in range(n - 2, -1, -1):
        for j in range(i + 1):  # 第 i 行有 i+1 个元素
            # 当前元素 + 下方两个相邻元素中较小的那个
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1])

    return dp[0]


if __name__ == "__main__":
    triangle = [[2], [3, 4], [6, 5, 7], [4, 1, 8, 3]]
    assert minimumTotal(triangle) == 11
    assert minimumTotal([[-10]]) == -10
