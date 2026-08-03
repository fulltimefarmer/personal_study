/**
 * 考点：数组、双指针、二分查找
 * 题目：Two Sum II - Input Array Is Sorted（两数之和 II - 输入有序数组）
 * 题目描述：在已排序数组中找到和为 target 的两个数，返回其下标（从 1 开始）。
 *   示例：numbers = [2,7,11,15], target = 9 → [1,2]
 * 思路：双指针。left 指向开头，right 指向末尾。
 *   sum < target → left++（需要更大的和）
 *   sum > target → right--（需要更小的和）
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function twoSum(numbers: number[], target: number): number[] {
  let left = 0;
  let right = numbers.length - 1;

  while (left < right) {
    const sum = numbers[left] + numbers[right];
    if (sum === target) {
      return [left + 1, right + 1];
    } else if (sum < target) {
      left++;
    } else {
      right--;
    }
  }

  return [];
}

export { twoSum };
