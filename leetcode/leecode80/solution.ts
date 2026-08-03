/**
 * 考点：Array, Two Pointers
 * 题目：Remove Duplicates from Sorted Array II（删除有序数组中的重复项 II）
 * 题目描述：原地删除有序数组中的重复项，使每个元素最多出现两次，返回新长度。
 * 示例：nums = [1,1,1,2,2,3] → 5, nums = [1,1,2,2,3]
 * 示例：nums = [0,0,1,1,1,1,2,3,3] → 7, nums = [0,0,1,1,2,3,3]
 * 思路：双指针。slow 指向写入位置，count 记录当前数字的出现次数。
 *       只有 count <= 2 时才写入，超过两次跳过。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function removeDuplicates(nums: number[]): number {
    if (nums.length <= 2) return nums.length;

    let slow = 1;
    let count = 1;

    for (let i = 1; i < nums.length; i++) {
        if (nums[i] === nums[i - 1]) {
            count++;
        } else {
            count = 1;
        }

        if (count <= 2) {
            nums[slow] = nums[i];
            slow++;
        }
    }

    return slow;
}

export { removeDuplicates };
