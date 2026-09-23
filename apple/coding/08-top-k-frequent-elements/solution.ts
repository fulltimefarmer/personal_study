// Top K Frequent Elements — 代码空壳（CoderPad 中填充）
// 返回出现频率前 k 高的元素，顺序不限。

function topKFrequent(nums: number[], k: number): number[] {
  // TODO: 统计频率，用桶排序（O(n)）或最小堆（O(n log k)）
  return [];
}

// —— 测试（可运行验证）——
function run() {
  console.log(JSON.stringify(topKFrequent([1, 1, 1, 2, 2, 3], 2).sort())); // [1,2]
  console.log(JSON.stringify(topKFrequent([1], 1)));                       // [1]
}

run();
