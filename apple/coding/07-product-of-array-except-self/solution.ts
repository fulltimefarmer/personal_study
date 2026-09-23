// Product of Array Except Self — 代码空壳（CoderPad 中填充）
// 返回 answer[i] = nums 中除 nums[i] 外所有元素的乘积，O(n) 时间、O(1) 额外空间、不用除法。

function productExceptSelf(nums: number[]): number[] {
  // TODO: 先算左侧积，再从右往左乘入右侧积
  return [];
}

// —— 测试（可运行验证）——
function run() {
  console.log(JSON.stringify(productExceptSelf([1, 2, 3, 4])));    // [24,12,8,6]
  console.log(JSON.stringify(productExceptSelf([-1, 1, 0, -3, 3]))); // [0,0,9,0,0]
}

run();
