# Clone Graph — 考点分析与解题思路

## 考点分析

1. **深拷贝 vs 浅拷贝**：不能简单复制 `neighbors` 数组（否则新旧图共享节点引用）。必须为每个原节点创建一个**值相同但引用全新**的新节点，并重建所有边。
2. **环与重复引用**：无向图天然存在「回头边」（A→B 且 B→A），若不记录映射会无限递归/重复建点。核心是用 `Map<oldNode, newNode>` 记录已克隆的节点，既是去重也是 visited。
3. **遍历方式**：DFS（递归/栈）与 BFS（队列）均可。DFS 更简洁，BFS 更贴近「逐层复制」的直觉，面试时二选一说清即可。

## 解题思路

### 方案 A：DFS + visited 哈希

- 若 `node === null` 返回 `null`。
- 若 `visited` 中已有该节点，直接返回其克隆（避免重复克隆/成环）。
- 否则 `clone = new Node(node.val)`，先放入 `visited`（**必须在遍历邻居之前**，否则成环时重复进入）。
- 对每个邻居递归克隆，并把结果 `push` 进 `clone.neighbors`。

### 方案 B：BFS + visited 哈希

- 用队列从起点逐层扩展；每弹出一个原节点，就克隆（若未克隆）并补齐其邻居的克隆与边。

## 复杂度

- 时间：O(V + E)，每个节点、每条边访问一次。
- 空间：O(V)，visited 哈希 + 递归栈 / 队列。

## 参考代码（DFS）

```ts
function cloneGraph(node: Node | null): Node | null {
  if (!node) return null;
  const visited = new Map<Node, Node>();

  function dfs(n: Node): Node {
    if (visited.has(n)) return visited.get(n)!;
    const clone = new Node(n.val);
    visited.set(n, clone);               // 先登记，防止环
    for (const nb of n.neighbors) {
      clone.neighbors.push(dfs(nb));
    }
    return clone;
  }

  return dfs(node);
}
```

## 参考代码（BFS）

```ts
function cloneGraph(node: Node | null): Node | null {
  if (!node) return null;
  const visited = new Map<Node, Node>();
  const queue: Node[] = [node];
  visited.set(node, new Node(node.val));

  while (queue.length) {
    const cur = queue.shift()!;
    for (const nb of cur.neighbors) {
      if (!visited.has(nb)) {
        visited.set(nb, new Node(nb.val));
        queue.push(nb);
      }
      visited.get(cur)!.neighbors.push(visited.get(nb)!);
    }
  }
  return visited.get(node)!;
}
```

## 追问 / Follow-ups

1. **有向图**能克隆吗？→ 完全一样，visited 哈希同样适用（有向图不会有回头边，但可能有共享子节点）。
2. **带随机指针的链表**（LeetCode 138 Copy List with Random Pointer）？→ 同构问题，用 `Map<old, new>` 一次遍历建映射、二次遍历接指针。
3. 为什么先 `visited.set` 再遍历邻居？→ 图有环时，若不先登记会重复克隆同一节点，导致错误结构或无限递归。
