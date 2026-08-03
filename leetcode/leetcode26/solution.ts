/**
 * 考点：Array, Two Pointers
 * 题目：Remove Duplicates from Sorted Array（删除有序数组中的重复项）
 * 题目描述：原地删除有序数组中的重复元素。如 [1,1,2] → 返回2, 前两个元素为 [1,2]
 * 思路：快慢指针，slow指向已去重末尾，fast遍历。遇不同元素则复制到slow+1。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function removeDuplicates(nums: number[]): number {
    if (nums.length === 0) return 0;

    let slow = 0;
    for (let fast = 1; fast < nums.length; fast++) {
        if (nums[fast] !== nums[slow]) {
            slow++;
            nums[slow] = nums[fast];
        }
    }
    return slow + 1;
}

export { removeDuplicates };
