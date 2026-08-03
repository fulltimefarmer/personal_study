/**
 * 考点：数组、双指针
 * 题目：Move Zeroes（移动零）
 * 题目描述：将所有 0 移动到数组末尾，同时保持非零元素的相对顺序，原地操作
 * 思路：双指针。慢指针指向下一个非零元素应放位置，快指针遍历数组，
 *       遇到非零元素就交换到慢指针位置，慢指针后移。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function moveZeroes(nums: number[]): void {
    let left = 0;

    for (let right = 0; right < nums.length; right++) {
        if (nums[right] !== 0) {
            [nums[left], nums[right]] = [nums[right], nums[left]];
            left++;
        }
    }
}

export { moveZeroes };
