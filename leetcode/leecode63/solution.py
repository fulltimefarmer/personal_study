"""
考点: Array, Dynamic Programming, Matrix
题目: Unique Paths II（不同路径 II）
题目描述: 机器人位于 m*n 网格左上角，每次只能向下或向右移动。网格中有障碍物(1)和空位(0)，求到达右下角的不同路径数。
示例: obstacleGrid = [[0,0,0],[0,1,0],[0,0,0]] -> 2
思路: 动态规划。若当前位置是障碍物，dp[j]=0；否则 dp[j] += dp[j-1]。空间优化为一维数组。
      起点/终点是障碍物直接返回 0。
时间复杂度: O(m * n)
空间复杂度: O(n)
"""


def uniquePathsWithObstacles(obstacleGrid: list[list[int]]) -> int:
    m = len(obstacleGrid)
    n = len(obstacleGrid[0])

    # 起点或终点有障碍物，无法到达
    if obstacleGrid[0][0] == 1 or obstacleGrid[m - 1][n - 1] == 1:
        return 0

    dp = [0] * n
    dp[0] = 1  # 起点只有一种走法（还未被障碍物阻挡）

    for i in range(m):
        for j in range(n):
            if obstacleGrid[i][j] == 1:
                # 障碍物: 无法通过此格，路径数为 0
                dp[j] = 0
            elif j > 0:
                # 空位: 路径数 = 上方(dp[j]旧值) + 左方(dp[j-1]新值)
                dp[j] += dp[j - 1]
            # j == 0 时: dp[0] 保持不变，因为第一列只能从上方来
            # 如果上方有障碍物，dp[0] 会被置为 0

    return dp[n - 1]


if __name__ == "__main__":
    assert uniquePathsWithObstacles([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == 2
    assert uniquePathsWithObstacles([[0, 1], [0, 0]]) == 1
    assert uniquePathsWithObstacles([[1, 0]]) == 0  # 起点有障碍
    assert uniquePathsWithObstacles([[0, 0], [1, 1], [0, 0]]) == 0  # 由障碍物完全阻断
