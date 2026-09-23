# Course Schedule — 考点分析与解题思路

## 考点分析

1. **问题建模为「有向图判环」**：课程是节点，先修关系是有向边 `b -> a`（先修 b 才能修 a）。「能完成所有课程」等价于「图中**不存在环**」。
2. **两种经典解法**：
   - **拓扑排序（Kahn 算法，BFS）**：不断删除入度为 0 的节点，若最后处理的节点数等于总数则无环。
   - **DFS 三色标记判环**：`0`=未访问，`1`=访问中（当前递归栈），`2`=已完成；若遇到「访问中」的节点则存在环。
3. **依赖方向要统一**：边方向约定为 `b -> a`（先修指向后修），入度数组才正确。
4. **边界**：无先修课程（全入度 0）、自环、孤立节点、成环。

## 解题思路（Kahn 拓扑排序）

1. 建邻接表 `adj` 与入度数组 `indegree`；对每条边 `[a, b]`：`adj[b].push(a)`，`indegree[a]++`。
2. 把所有入度为 0 的节点入队。
3. 队列不空时出队，计数 `visited++`；对其每个邻居，入度减 1，若变 0 则入队。
4. 返回 `visited === numCourses`（相等则无环，能完成）。

## 复杂度

- 时间：O(V + E)，V = numCourses，E = prerequisites.length。
- 空间：O(V + E)，邻接表 + 队列。

## 参考代码（Kahn / BFS 拓扑排序）

```ts
function canFinish(numCourses: number, prerequisites: number[][]): boolean {
  const adj: number[][] = Array.from({ length: numCourses }, () => []);
  const indegree = new Array(numCourses).fill(0);

  for (const [a, b] of prerequisites) {
    adj[b].push(a);          // 先修 b -> a
    indegree[a]++;
  }

  const queue: number[] = [];
  for (let i = 0; i < numCourses; i++) {
    if (indegree[i] === 0) queue.push(i);
  }

  let visited = 0;
  while (queue.length) {
    const node = queue.shift()!;
    visited++;
    for (const next of adj[node]) {
      if (--indegree[next] === 0) queue.push(next);
    }
  }

  return visited === numCourses;
}
```

## 参考代码（DFS 三色标记判环）

```ts
function canFinish(numCourses: number, prerequisites: number[][]): boolean {
  const adj: number[][] = Array.from({ length: numCourses }, () => []);
  for (const [a, b] of prerequisites) adj[b].push(a);

  const state = new Array(numCourses).fill(0); // 0 未访问 / 1 访问中 / 2 完成

  const hasCycle = (node: number): boolean => {
    if (state[node] === 1) return true;   // 回到递归栈 → 环
    if (state[node] === 2) return false;  // 已处理，无环
    state[node] = 1;
    for (const next of adj[node]) {
      if (hasCycle(next)) return true;
    }
    state[node] = 2;
    return false;
  };

  for (let i = 0; i < numCourses; i++) {
    if (hasCycle(i)) return false;
  }
  return true;
}
```

## 追问 / Follow-ups

1. **课程表 II**（LeetCode 210）：要求返回一个可行的修课顺序 → Kahn 算法出队顺序即为拓扑序，若 `visited < n` 则返回空。
2. **并查集**能解吗？→ 不能，并查集适合**无向图**连通性/成环，无法处理**有向**依赖环。
3. 若要求返回所有拓扑序？→ 回溯枚举，但可能指数级。
4. 环的检测还有哪些方法？→ 拓扑排序、DFS 三色、强连通分量（Kosaraju/Tarjan）。
