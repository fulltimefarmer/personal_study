"""
考点: Array, Dynamic Programming, Matrix
题目: Minimum Path Sum（最小路径和）
题目描述: 给定 m*n 非负整数网格，每次只能向下或向右移动，求从左上角到右下角的最小路径和。
示例: grid = [[1,3,1],[1,5,1],[4,2,1]] -> 7
思路: 动态规划，原地修改 grid。dp[i][j] = grid[i][j] + min(上方, 左方)。
时间复杂度: O(m * n)
空间复杂度: O(1)
"""


def minPathSum(grid: list[list[int]]) -> int:
    m = len(grid)
    n = len(grid[0])

    # 初始化第一行: 每个格子只能从左边到达，所以累加
    for j in range(1, n):
        grid[0][j] += grid[0][j - 1]

    # 初始化第一列: 每个格子只能从上方到达，所以累加
    for i in range(1, m):
        grid[i][0] += grid[i - 1][0]

    # 动态规划填充剩余格子
    for i in range(1, m):
        for j in range(1, n):
            # 到达 (i,j) 的最小路径和 = 当前值 + min(上方路径和, 左方路径和)
            grid[i][j] += min(grid[i - 1][j], grid[i][j - 1])

    return grid[m - 1][n - 1]


if __name__ == "__main__":
    assert minPathSum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    assert minPathSum([[1, 2, 3], [4, 5, 6]]) == 12
    assert minPathSum([[1]]) == 1
