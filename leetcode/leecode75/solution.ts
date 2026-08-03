/**
 * 考点：Array, Two Pointers, Sorting
 * 题目：Sort Colors（颜色分类）
 * 题目描述：给定只含 0,1,2 的数组 nums，原地排序使 0 在前、1 在中、2 在后。
 * 示例：nums = [2,0,2,1,1,0] → [0,0,1,1,2,2]
 * 思路：三指针（荷兰国旗问题）。p0 指向 0 的右边界，p2 指向 2 的左边界，curr 扫描。
 *       nums[curr]==0 时与 p0 交换并前进；nums[curr]==2 时与 p2 交换但不前进（需再检查）；
 *       nums[curr]==1 时直接前进。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function sortColors(nums: number[]): void {
    let p0 = 0;
    let curr = 0;
    let p2 = nums.length - 1;

    while (curr <= p2) {
        if (nums[curr] === 0) {
            [nums[curr], nums[p0]] = [nums[p0], nums[curr]];
            p0++;
            curr++;
        } else if (nums[curr] === 2) {
            [nums[curr], nums[p2]] = [nums[p2], nums[curr]];
            p2--;
        } else {
            curr++;
        }
    }
}

export { sortColors };
