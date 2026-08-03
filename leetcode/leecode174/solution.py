"""
考点：数组、动态规划、矩阵
题目：Dungeon Game（地下城游戏）
思路：反向 DP，从右下向左上递推。dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - dungeon[i][j])。
      一维数组优化空间。
时间复杂度：O(m × n)
空间复杂度：O(n)
"""


def calculateMinimumHP(dungeon: list[list[int]]) -> int:
    m = len(dungeon)
    n = len(dungeon[0])
    # dp[j] 表示从当前位置到终点所需的最小生命值
    # 初始化为正无穷，dp[n] 作为哨兵，dp[n-1] 设为 1
    dp: list[float] = [float("inf")] * (n + 1)
    dp[n - 1] = 1  # 到达公主时至少需要 1 点生命

    # 从下到上、从右到左反向递推
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            # 选择右边或下边所需生命值较小的路径
            # 减去当前格的值（正数为加血，负数为扣血）
            need = min(dp[j], dp[j + 1]) - dungeon[i][j]
            # 生命值至少为 1
            dp[j] = max(1, need)

    return int(dp[0])


if __name__ == "__main__":
    # 示例: dungeon=[[-2,-3,3],[-5,-10,1],[10,30,-5]] → 7
    dungeon = [[-2, -3, 3], [-5, -10, 1], [10, 30, -5]]
    assert calculateMinimumHP(dungeon) == 7
    print("全部测试通过")
