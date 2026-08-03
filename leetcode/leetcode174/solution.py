"""
考点：数组、动态规划
题目：Dungeon Game（地下城游戏）
题目描述：给定二维网格 dungeon，骑士从左上角出发到右下角，途经每个格子会增减生命值。
  求骑士起始至少需要多少生命值，才能保证在任意时刻生命值 > 0。
  示例：dungeon = [[-2,-3,3],[-5,-10,1],[10,30,-5]] → 7
思路：逆向动态规划。从右下角向左上角反推。
  dp[i][j] 表示从 (i,j) 到达右下角所需的最小初始生命值。
  对于每个格子，骑士需要 min_health = min(dp[i+1][j], dp[i][j-1]) - dungeon[i][j]。
  如果 min_health <= 0 说明这个格子提供的生命足够后续使用，只需保持 1 点生命。
时间复杂度：O(m*n)
空间复杂度：O(m*n)，可优化到 O(n)
"""


def calculateMinimumHP(dungeon: list[list[int]]) -> int:
    m = len(dungeon)
    n = len(dungeon[0])

    # dp[i][j]：从 (i,j) 出发到达右下角所需的最小初始生命值
    # 多申请一行一列用无穷大填充边界，方便处理
    dp = [[float("inf")] * (n + 1) for _ in range(m + 1)]
    # 右下角格子的「下方」和「右方」初始化为 1
    # 因为到达终点后，至少需要 1 点生命
    dp[m][n - 1] = dp[m - 1][n] = 1

    # 从右下角往左上角逆推
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            # 选择从当前格子去往「下方」或「右方」中所需初始生命更小的方向
            min_health = min(dp[i + 1][j], dp[i][j + 1]) - dungeon[i][j]
            # 如果 min_health <= 0，说明当前格子的补给足够覆盖后续所有消耗
            # 此时只需保持 1 点生命即可（不能为 0 或负数）
            dp[i][j] = max(min_health, 1)

    return dp[0][0]


if __name__ == "__main__":
    dungeon1 = [[-2, -3, 3], [-5, -10, 1], [10, 30, -5]]
    assert calculateMinimumHP(dungeon1) == 7
    assert calculateMinimumHP([[0]]) == 1
