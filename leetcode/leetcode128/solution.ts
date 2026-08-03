/**
 * 考点：并查集、数组、哈希表
 * 题目：Longest Consecutive Sequence（最长连续序列）
 * 题目描述：未排序数组中找出最长连续序列的长度。要求 O(n)。
 *   示例：nums = [100,4,200,1,3,2] → 4（序列 [1,2,3,4]）
 * 思路：哈希集合。只从连续序列的起点（num-1 不在集合中）开始计数。
 *   虽然内层 while，但每个数只被访问一次，总体 O(n)。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */

function longestConsecutive(nums: number[]): number {
  const numSet = new Set(nums);
  let maxLen = 0;

  for (const num of numSet) {
    if (!numSet.has(num - 1)) {
      let currentNum = num;
      let currentLen = 1;

      while (numSet.has(currentNum + 1)) {
        currentNum++;
        currentLen++;
      }

      maxLen = Math.max(maxLen, currentLen);
    }
  }

  return maxLen;
}

export { longestConsecutive };
