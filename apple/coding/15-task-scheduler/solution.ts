// Task Scheduler — 代码空壳（CoderPad 中填充）
// 计算完成所有任务（含冷却时间）所需的最短时间。

function leastInterval(tasks: string[], n: number): number {
  // TODO: 统计频率，用公式 max(len, (maxCount-1)*(n+1)+numMax)
  return 0;
}

// —— 测试（可运行验证）——
function run() {
  console.log(leastInterval(["A", "A", "A", "B", "B", "B"], 2)); // 8
  console.log(leastInterval(["A", "A", "A", "B", "B", "B"], 0)); // 6
  console.log(leastInterval(["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2)); // 16
}

run();
