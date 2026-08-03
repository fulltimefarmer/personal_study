/**
 * 考点：位运算、数组
 * 题目：Single Number（只出现一次的数字）
 * 题目描述：非空数组中除了一个元素只出现一次外，其余都出现两次。找到那个只出现一次的元素。
 *   示例：nums = [4,1,2,1,2] → 4
 * 思路：异或运算。a ⊕ a = 0，a ⊕ 0 = a，满足交换律和结合律。
 *   所有元素异或，成对的互相抵消，最终结果就是唯一出现一次的数。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function singleNumber(nums: number[]): number {
  let result = 0;
  for (const num of nums) {
    result ^= num;
  }
  return result;
}

export { singleNumber };
