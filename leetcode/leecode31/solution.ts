/**
 * 考点：Array, Two Pointers
 * 题目：Next Permutation（下一个排列）
 * 题目描述：原地将数组重新排列为字典序的下一个更大排列，如果不存在则重排为最小排列。
 * 示例：nums = [1,2,3] => [1,3,2]
 * 思路：从右找第一个相邻升序对，再找右边大于较小数的数，交换后反转后半部分
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

/**
 Do not return anything, modify nums in-place instead.
 */
function nextPermutation(nums: number[]): void {
    const n = nums.length;
    let i = n - 2;

    while (i >= 0 && nums[i] >= nums[i + 1]) {
        i--;
    }

    if (i >= 0) {
        let j = n - 1;
        while (j >= 0 && nums[j] <= nums[i]) {
            j--;
        }
        [nums[i], nums[j]] = [nums[j], nums[i]];
    }

    let left = i + 1;
    let right = n - 1;
    while (left < right) {
        [nums[left], nums[right]] = [nums[right], nums[left]];
        left++;
        right--;
    }
}
export { nextPermutation };
