// Flatten Array — 代码空壳（CoderPad 中填充）
// 展平嵌套数组，depth 默认 1，Infinity 表示完全展平。

function flatten(arr: any[], depth = 1): any[] {
  // TODO: 递归或迭代，遇到数组且 depth>0 则继续展平
  return [];
}

// —— 测试（可运行验证）——
function run() {
  console.log(JSON.stringify(flatten([1, 2, [3, 4]])));                     // [1,2,3,4]
  console.log(JSON.stringify(flatten([1, [2, [3, [4]]]], 1)));              // [1,2,[3,[4]]]
  console.log(JSON.stringify(flatten([1, [2, [3, [4]]]], 2)));              // [1,2,3,[4]]
  console.log(JSON.stringify(flatten([1, [2, [3, [4]]]], Infinity)));       // [1,2,3,4]
  console.log(JSON.stringify(flatten([1, [2, 3]], 0)));                     // [1,[2,3]]
  console.log(JSON.stringify(flatten([])));                                 // []
}

run();
