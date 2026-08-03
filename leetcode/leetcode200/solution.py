"""
考点：深度优先搜索、广度优先搜索、并查集
题目：Number of Islands（岛屿数量）
题目描述：给定二维网格 grid（'1' 陆地，'0' 水域），计算岛屿数量（相邻陆地组成一个岛屿）。
  示例：grid = [
    ["1","1","0","0","0"],
    ["1","1","0","0","0"],
    ["0","0","1","0","0"],
    ["0","0","0","1","1"]
  ] → 3
思路：DFS 遍历网格。遇到 '1' 时岛屿计数 +1，然后 DFS 将相连的所有 '1' 标记为 '0'（沉岛）。
  相当于把整个岛屿「淹没」，避免重复计数。
时间复杂度：O(m*n)
空间复杂度：O(m*n)（递归栈），或可改写为迭代 BFS 控制栈深
"""


def numIslands(grid: list[list[str]]) -> int:
    m = len(grid)
    n = len(grid[0])

    def dfs(i: int, j: int) -> None:
        """深度优先搜索，把 (i,j) 所在岛屿的所有陆地 '1' 沉为 '0'"""
        # 边界检查：越界或在水中则返回
        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] == "0":
            return
        # 将当前陆地沉没，避免重复访问
        grid[i][j] = "0"
        # 向四个方向继续淹没相连陆地
        dfs(i + 1, j)  # 下
        dfs(i - 1, j)  # 上
        dfs(i, j + 1)  # 右
        dfs(i, j - 1)  # 左

    count = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == "1":  # 发现新岛屿
                count += 1
                dfs(i, j)  # 淹没整个岛屿

    return count


if __name__ == "__main__":
    grid1 = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert numIslands(grid1) == 3

    grid2 = [
        ["1", "1", "1"],
        ["0", "1", "0"],
        ["1", "1", "1"],
    ]
    assert numIslands(grid2) == 1
