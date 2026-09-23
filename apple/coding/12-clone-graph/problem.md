# Clone Graph · 克隆图

- **LeetCode:** 133
- **难度 Difficulty:** Medium
- **标签 Topics:** 图 / 深度优先搜索 / 广度优先搜索 / 哈希表 / Graph / DFS / BFS / Hash Table
- **苹果频率:** 高频（Educative/候选面经均列为 Apple 图类常考题）

## 题干（中文）

给你无向**连通**图中的一个节点的引用，请你返回该图的**深拷贝**（克隆）。

图中的每个节点都包含它的值 `val` 和其邻居的列表（`neighbors`）。

```ts
class Node {
  val: number;
  neighbors: Node[];
}
```

## Problem Statement (English)

Given a reference of a node in a **connected** undirected graph, return a **deep copy** (clone) of the graph.

Each node in the graph contains a value (`int`) and a list (`List[Node]`) of its neighbors.

```ts
class Node {
  val: number;
  neighbors: Node[];
}
```

## 示例 / Examples

```
输入 / Input:  adjList = [[2,4],[1,3],[2,4],[1,3]]
输出 / Output: [[2,4],[1,3],[2,4],[1,3]]
// 1 --- 2
// |     |
// 4 --- 3   （每个节点值唯一，clone 结构相同）

输入 / Input:  adjList = [[]]
输出 / Output: [[]]   // 单个节点，无邻居

输入 / Input:  adjList = []
输出 / Output: []     // 空图
```

## 约束 / Constraints

- 图中节点的数量在 `[0, 100]` 范围内
- `1 <= Node.val <= 100`
- `Node.val` 是唯一的
- 无重复边与自环
- 图是连通图（或空图）

## 测试格式 / Test Format

为简单起见，每个节点的值与它的索引相同（从 1 开始）。`adjList` 表示每个节点的邻居列表。你的克隆必须返回与输入图结构相同的副本（节点的 `val` 相同，但引用是全新的）。
