// Clone Graph — 代码空壳（CoderPad 中填充）
// 深拷贝无向连通图，返回克隆节点。

class Node {
  val: number;
  neighbors: Node[];
  constructor(val?: number, neighbors?: Node[]) {
    this.val = val === undefined ? 0 : val;
    this.neighbors = neighbors === undefined ? [] : neighbors;
  }
}

function cloneGraph(node: Node | null): Node | null {
  // TODO: 用 Map<原节点, 克隆节点> 做 visited，DFS 或 BFS 克隆
  return null;
}

// —— 测试（可运行验证）——
function buildGraph(adj: number[][]): Node | null {
  if (adj.length === 0) return null;
  const nodes: Node[] = adj.map((_, i) => new Node(i + 1));
  adj.forEach((neighbors, i) => {
    nodes[i].neighbors = neighbors.map(idx => nodes[idx - 1]);
  });
  return nodes[0];
}

function serialize(node: Node | null): number[][] {
  if (!node) return [];
  const visited = new Map<Node, number>();
  const res: number[][] = [];
  const queue: Node[] = [node];
  while (queue.length) {
    const cur = queue.shift()!;
    if (visited.has(cur)) continue;
    visited.set(cur, res.length);
    res.push(cur.neighbors.map(n => n.val));
    for (const nb of cur.neighbors) if (!visited.has(nb)) queue.push(nb);
  }
  return res;
}

function run() {
  const g1 = buildGraph([[2, 4], [1, 3], [2, 4], [1, 3]]);
  console.log(JSON.stringify(serialize(cloneGraph(g1)))); // [[2,4],[1,3],[2,4],[1,3]]
  const g2 = buildGraph([[]]);
  console.log(JSON.stringify(serialize(cloneGraph(g2)))); // [[]]
  console.log(JSON.stringify(serialize(cloneGraph(null)))); // []
}

run();
