/**
 * 考点：Array, Two Pointers
 * 题目：Remove Duplicates from Sorted Array（删除有序数组中的重复项）
 * 题目描述：原地删除有序数组中的重复项，使每个元素只出现一次，返回新长度。
 * 示例：nums = [0,0,1,1,1,2,2,3,3,4] => 5, nums = [0,1,2,3,4,...]
 * 思路：快慢指针，慢指针指向已去重末尾，快指针遍历，遇到不同元素时覆盖到慢指针位置
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function removeDuplicates(nums: number[]): number {
    if (nums.length === 0) return 0;

    let k = 0;

    for (let i = 1; i < nums.length; i++) {
        if (nums[i] !== nums[k]) {
            k++;
            nums[k] = nums[i];
        }
    }

    return k + 1;
}
export { removeDuplicates };
