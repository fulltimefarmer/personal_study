/**
 * 考点：Array, Two Pointers
 * 题目：Remove Element（移除元素）
 * 题目描述：原地移除数组中所有等于 val 的元素，返回移除后数组新长度。
 * 示例：nums = [3,2,2,3], val = 3 => 2, nums = [2,2,...]
 * 思路：快慢指针，快指针遍历，遇到不等于 val 的元素覆盖到慢指针位置
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function removeElement(nums: number[], val: number): number {
    let k = 0;

    for (let i = 0; i < nums.length; i++) {
        if (nums[i] !== val) {
            nums[k] = nums[i];
            k++;
        }
    }

    return k;
}
export { removeElement };
