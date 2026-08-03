/**
 * 考点：Array, Two Pointers
 * 题目：Next Permutation（下一个排列）
 * 题目描述：将数组原地重排为下一个字典序更大的排列。如 [1,2,3] → [1,3,2]
 * 思路：从右找到第一个断点nums[i]<nums[i+1]，找右侧比nums[i]大的最小值交换，反转右侧。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
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
