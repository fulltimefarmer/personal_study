/**
 * 考点：Array, Two Pointers, Binary Search
 * 题目：Two Sum II - Input Array Is Sorted（两数之和II）
 * 题目描述：有序数组找两数之和为 target，返回下标（1-based）。唯一答案，O(1) 额外空间。
 * 示例 1：[2,7,11,15], target=9，输出 [1,2]
 * 示例 2：[2,3,4], target=6，输出 [1,3]
 * 示例 3：[-1,0], target=-1，输出 [1,2]
 * 思路：双指针，和小则左指针右移，和大则右指针左移。
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

    return [-1, -1];
}

export { twoSum };
