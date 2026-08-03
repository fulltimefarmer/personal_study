"""
考点：DFS、BFS、并查集、数组、矩阵
题目：Number of Islands（岛屿数量）
思路：遍历网格，遇到 '1' 计数+1，DFS 将相连陆地全部标记为 '0'（沉岛法）。
时间复杂度：O(m × n)
空间复杂度：O(m × n)（递归栈最深可达整个网格）
"""


def numIslands(grid: list[list[str]]) -> int:
    m = len(grid)
    n = len(grid[0])
    count = 0

    def dfs(i: int, j: int) -> None:
        """深度优先搜索，将 (i,j) 连接的整片陆地沉没（标记为 '0'）"""
        # 越界或遇到水域则返回
        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] == "0":
            return
        # 将当前陆地沉没，防止重复访问
        grid[i][j] = "0"
        # 向四个方向递归探索
        dfs(i - 1, j)  # 上
        dfs(i + 1, j)  # 下
        dfs(i, j - 1)  # 左
        dfs(i, j + 1)  # 右

    for i in range(m):
        for j in range(n):
            if grid[i][j] == "1":
                count += 1  # 发现新岛屿
                dfs(i, j)   # 沉没整个岛屿

    return count


if __name__ == "__main__":
    # 示例: 3 个岛屿（间隔分布）
    grid = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert numIslands(grid) == 3
    print("全部测试通过")
