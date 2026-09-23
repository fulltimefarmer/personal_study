# Number of Islands · 岛屿数量

- **LeetCode:** 200
- **难度 Difficulty:** Medium
- **标签 Topics:** 图 / 深度优先搜索 / 广度优先搜索 / DFS / BFS / Graph
- **苹果频率:** 高频（Apple #4）

## 题干（中文）

给你一个由 `'1'`（陆地）和 `'0'`（水）组成的二维网格 `grid`，请你计算网格中岛屿的数量。

岛屿总是被水包围，并且每座岛屿只能由**水平方向或垂直方向**相邻的陆地连接形成。你可以假设网格的四条边均被水包围。

## Problem Statement (English)

Given an `m x n` 2D binary grid `grid` which represents a map of `'1'`s (land) and `'0'`s (water), return the number of islands.

An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically. You may assume all four edges of the grid are all surrounded by water.

## 示例 / Examples

```
输入 / Input:
grid = [
  ["1","1","1","1","0"],
  ["1","1","0","1","0"],
  ["1","1","0","0","0"],
  ["0","0","0","0","0"]
]
输出 / Output: 1

输入 / Input:
grid = [
  ["1","1","0","0","0"],
  ["1","1","0","0","0"],
  ["0","0","1","0","0"],
  ["0","0","0","1","1"]
]
输出 / Output: 3
```

## 约束 / Constraints

- `m == grid.length`, `n == grid[i].length`
- `1 <= m, n <= 300`
- `grid[i][j]` 是 `'0'` 或 `'1'`
