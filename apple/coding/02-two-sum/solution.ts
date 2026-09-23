// Two Sum — 代码空壳（CoderPad 中填充）
// 返回和为目标值的两个元素下标。

function twoSum(nums: number[], target: number): number[] {
  const seen = new Map<number, number>();
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (seen.has(complement)) {
      return [i, seen.get(complement)!];
    }
    seen.set(nums[i], i);
  }
  return [];
}

// —— 测试（可运行验证）——
function run() {
  console.log(twoSum([2, 7, 11, 15], 9)); // [0,1]
  console.log(twoSum([3, 2, 4], 6));      // [1,2]
  console.log(twoSum([3, 3], 6));         // [0,1]
}

run();
