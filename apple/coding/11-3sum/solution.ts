// 3Sum — 代码空壳（CoderPad 中填充）
// 返回所有和为 0 且不重复的三元组。

function threeSum(nums: number[]): number[][] {
  // TODO: 排序 + 固定一个数 + 首尾双指针，注意去重
  return [];
}

// —— 测试（可运行验证）——
function run() {
  const sort3 = (arr: number[][]) =>
    arr.map(t => t.sort((a, b) => a - b)).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);

  console.log(JSON.stringify(sort3(threeSum([-1, 0, 1, 2, -1, -4])))); // [[-1,-1,2],[-1,0,1]]
  console.log(JSON.stringify(sort3(threeSum([0, 1, 1]))));            // []
  console.log(JSON.stringify(sort3(threeSum([0, 0, 0]))));            // [[0,0,0]]
}

run();
