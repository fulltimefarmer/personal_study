/**
 * 考点：数组、哈希表（原地标记）
 * 题目：Find All Numbers Disappeared in an Array（找到所有数组中消失的数字）
 * 题目描述：找出 [1, n] 中未出现在数组 nums 中的数字
 * 思路：原地标记。遍历数组，将 nums[abs(nums[i]) - 1] 标记为负数。
 *       再遍历一次，正数位置的索引 + 1 即为缺失数字。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function findDisappearedNumbers(nums: number[]): number[] {
    for (let i = 0; i < nums.length; i++) {
        const index = Math.abs(nums[i]) - 1;
        if (nums[index] > 0) {
            nums[index] = -nums[index];
        }
    }

    const result: number[] = [];
    for (let i = 0; i < nums.length; i++) {
        if (nums[i] > 0) {
            result.push(i + 1);
        }
    }

    return result;
}

export { findDisappearedNumbers };
