# Number of Islands — 考点分析与解题思路

## 考点分析

1. **图的连通分量计数**：把网格看成图，`'1'` 是节点，上下左右相邻的 `'1'` 之间有边。求「连通分量」的个数。
2. **DFS/BFS 淹没(flood fill)**：每遇到一个未访问的 `'1'`，计数 +1，并用 DFS/BFS 把与之相连的所有陆地标记为已访问（可原地改 `'0'` 或 `visited` 数组，避免额外空间）。
3. **原地标记**：直接把访问过的 `'1'` 改成 `'0'`（或其它非 `'1'` 字符），省掉 visited 二维数组，是常见优化。
4. **边界**：网格越界判断、`grid[i][j] !== '1'` 提前返回、m 或 n 为 1、全部是水、全部是陆地。
5. DFS 递归深度可能到 `m * n`（如蛇形陆地），JS 递归可能爆栈——可改用 BFS（显式队列）更稳；或迭代 DFS 用显式栈。

## 解题思路（DFS）

1. 遍历每个格子，若为 `'1'`：
   - `count++`；
   - 调用 `dfs(i, j)` 把整座岛「淹没」（置为 `'0'`）。
2. `dfs(i, j)`：
   - 越界或 `grid[i][j] !== '1'` → 返回；
   - `grid[i][j] = '0'`；
   - 对上下左右四个方向递归 `dfs`。
3. 返回 `count`。

## 复杂度

- 时间：O(m × n)，每个格子访问常数次。
- 空间：O(m × n)（DFS 递归栈最坏）或 O(m × n)（BFS 队列）；原地标记则无额外 visited 空间。

## 参考代码（DFS，原地标记）

```ts
function numIslands(grid: string[][]): number {
  const m = grid.length;
  const n = grid[0].length;
  let count = 0;

  const dfs = (i: number, j: number): void => {
    if (i < 0 || i >= m || j < 0 || j >= n || grid[i][j] !== '1') return;
    grid[i][j] = '0';                       // 淹没，标记已访问
    dfs(i + 1, j);
    dfs(i - 1, j);
    dfs(i, j + 1);
    dfs(i, j - 1);
  };

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (grid[i][j] === '1') {
        count++;
        dfs(i, j);
      }
    }
  }

  return count;
}
```

## 参考代码（BFS，避免递归爆栈）

```ts
function numIslands(grid: string[][]): number {
  const m = grid.length;
  const n = grid[0].length;
  const dirs = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let count = 0;

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (grid[i][j] !== '1') continue;
      count++;
      const queue: [number, number][] = [[i, j]];
      grid[i][j] = '0';
      while (queue.length) {
        const [x, y] = queue.shift()!;
        for (const [dx, dy] of dirs) {
          const nx = x + dx, ny = y + dy;
          if (nx >= 0 && nx < m && ny >= 0 && ny < n && grid[nx][ny] === '1') {
            grid[nx][ny] = '0';
            queue.push([nx, ny]);
          }
        }
      }
    }
  }

  return count;
}
```

## 参考代码（并查集 Union-Find）

并查集解法：把每个 `'1'` 格子看成一个集合，与其**左侧/上方**的相邻陆地合并（只查两个方向即可避免重复），最后统计根节点（`parent[i] === i` 且该格子是陆地）的数量。适合「动态添加陆地」的变体（LeetCode 305）。

```ts
class UnionFind {
  parent: number[];
  rank: number[];
  count = 0; // 连通分量（岛屿）数量

  constructor(grid: string[][]) {
    const m = grid.length, n = grid[0].length;
    this.parent = new Array(m * n).fill(0);
    this.rank = new Array(m * n).fill(0);
    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        if (grid[i][j] === '1') {
          const id = i * n + j;
          this.parent[id] = id;
          this.count++;
        }
      }
    }
  }

  find(x: number): number {
    if (this.parent[x] !== x) this.parent[x] = this.find(this.parent[x]); // 路径压缩
    return this.parent[x];
  }

  union(x: number, y: number): void {
    const rx = this.find(x), ry = this.find(y);
    if (rx === ry) return;
    if (this.rank[rx] < this.rank[ry]) this.parent[rx] = ry;
    else if (this.rank[rx] > this.rank[ry]) this.parent[ry] = rx;
    else { this.parent[ry] = rx; this.rank[rx]++; }
    this.count--; // 合并一次，岛屿减少一个
  }
}

function numIslands(grid: string[][]): number {
  const m = grid.length, n = grid[0].length;
  const uf = new UnionFind(grid);
  const dirs = [[1, 0], [0, 1]]; // 只向下、向右合并，避免重复
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (grid[i][j] !== '1') continue;
      for (const [dx, dy] of dirs) {
        const x = i + dx, y = j + dy;
        if (x < m && y < n && grid[x][y] === '1') {
          uf.union(i * n + j, x * n + y);
        }
      }
    }
  }
  return uf.count;
}
```

复杂度：时间 O(m × n × α)，α 为阿克曼反函数（近似常数）；空间 O(m × n)。

## 追问 / Follow-ups

1. **不修改原数组**（保留输入）→ 用 `visited` 布尔二维数组。
2. **岛屿最大面积**（LeetCode 695）→ 记录每次 DFS/BFS 的格子数取最大。
3. **岛屿周长**（LeetCode 463）→ 统计每个陆地格的「临水边」。
4. **闭合岛屿 / 被包围区域**（LeetCode 1254 / 130）→ 从边界陆地开始淹没，再统计内部。
5. **动态添加陆地**（LeetCode 305）→ 并查集天然适合：每次 `addLand` 时与四邻合并。
6. DFS 递归爆栈如何规避？→ 用 BFS 或迭代 DFS（显式栈）。
7. DFS/BFS vs 并查集如何选？→ 静态一次性统计用 DFS/BFS（简单）；需要动态增删/多次查询连通性用并查集。
