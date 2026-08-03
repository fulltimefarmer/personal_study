/**
 * 考点：数组、哈希表、分治、计数、排序
 * 题目：Majority Element（多数元素）
 * 题目描述：找出数组中出现次数超过 n/2 的元素。题目保证多数元素存在。
 *   示例：nums = [3,2,3] → 3
 * 思路：Boyer-Moore 投票算法。利用多数元素数量 > n/2 的特性，通过抵消法找出。
 *   candidate 记录候选元素，count 记录票数。遇到相同元素 count++，不同 count--。
 *   count 归零时更换 candidate。最终 candidate 即为多数元素。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function majorityElement(nums: number[]): number {
  let candidate = nums[0];
  let count = 1;

  for (let i = 1; i < nums.length; i++) {
    if (count === 0) {
      candidate = nums[i];
      count = 1;
    } else if (nums[i] === candidate) {
      count++;
    } else {
      count--;
    }
  }

  return candidate;
}

export { majorityElement };
