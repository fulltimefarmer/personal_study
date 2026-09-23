// Course Schedule — 代码空壳（CoderPad 中填充）
// 判断是否能完成所有课程（等价于先修关系构成的有向图无环）。

function canFinish(numCourses: number, prerequisites: number[][]): boolean {
  // TODO: 建邻接表 + 入度，用 Kahn 拓扑排序或 DFS 三色判环
  return false;
}

// —— 测试（可运行验证）——
function run() {
  console.log(canFinish(2, [[1, 0]]));        // true
  console.log(canFinish(2, [[1, 0], [0, 1]])); // false（成环）
  console.log(canFinish(4, [[1, 0], [2, 1], [3, 2]])); // true
}

run();
