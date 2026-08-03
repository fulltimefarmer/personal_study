"""
考点：动态规划
题目：Knight Probability in Chessboard（骑士在棋盘上的概率）
题目描述：骑士从 (row,column) 开始，每次随机走 8 个方向之一，走 k 步。求 k 步后仍在棋盘上的概率。
思路：DP。dp[step][r][c] 表示 step 步后在 (r,c) 的概率。dp[step+1][nr][nc] += dp[step][r][c]/8。最终求和。用滚动数组优化空间。
时间复杂度：O(k * n²)
空间复杂度：O(n²)
"""


def knightProbability(n: int, k: int, row: int, column: int) -> float:
    # 骑士的 8 个可能移动方向：(行变化, 列变化)
    directions = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

    # dp[r][c] 表示当前步数下骑士在 (r,c) 的概率
    dp = [[0.0] * n for _ in range(n)]
    dp[row][column] = 1.0  # 初始位置概率为 1

    # 模拟 k 步移动
    for _ in range(k):
        # next_dp 记录下一步的概率分布，初始全为 0
        next_dp = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                if dp[r][c] == 0:
                    continue  # 跳过概率为 0 的位置，优化性能
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        # 从 (r,c) 以 1/8 的概率走到 (nr,nc)
                        # next_dp[nr][nc] 累加来自各个方向的概率
                        next_dp[nr][nc] += dp[r][c] / 8.0
        # 滚动更新，next_dp 成为下一轮的 dp
        dp = next_dp

    # 汇总 k 步后所有位置上仍在棋盘的概率（即所有单元格概率之和）
    return sum(sum(row) for row in dp)


if __name__ == "__main__":
    # 示例：n=3, k=2, row=0, column=0 → 输出: 0.0625
    result = knightProbability(3, 2, 0, 0)
    assert abs(result - 0.0625) < 1e-6
    # 示例：n=1, k=0, row=0, column=0 → 输出: 1.0
    assert knightProbability(1, 0, 0, 0) == 1.0
