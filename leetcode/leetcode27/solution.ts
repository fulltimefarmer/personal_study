/**
 * 考点：Array, Two Pointers
 * 题目：Remove Element（移除元素）
 * 题目描述：原地移除数组中等于val的元素，返回剩余元素个数。如 [3,2,2,3], val=3 → 返回2, [2,2,...]
 * 思路：快慢指针，fast遍历，遇到不等于val的元素复制到slow位置。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function removeElement(nums: number[], val: number): number {
    let slow = 0;
    for (let fast = 0; fast < nums.length; fast++) {
        if (nums[fast] !== val) {
            nums[slow] = nums[fast];
            slow++;
        }
    }
    return slow;
}

export { removeElement };
