// Merge Intervals — 代码空壳（CoderPad 中填充）
// 合并所有重叠区间，返回不重叠的区间数组。

function merge(intervals: number[][]): number[][] {
  // TODO: 先按 start 排序，再线性扫描合并
  return [];
}

// —— 测试（可运行验证）——
function run() {
  console.log(JSON.stringify(merge([[1, 3], [2, 6], [8, 10], [15, 18]]))); // [[1,6],[8,10],[15,18]]
  console.log(JSON.stringify(merge([[1, 4], [4, 5]])));                     // [[1,5]]
  console.log(JSON.stringify(merge([[1, 4], [2, 3]])));                     // [[1,4]]
}

run();
