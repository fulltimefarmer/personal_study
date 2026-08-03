/**
 * 考点：数组
 * 题目：Summary Ranges（汇总区间）
 * 题目描述：将有序无重复数组汇总为区间列表。nums=[0,1,2,4,5,7] 输出 ["0->2","4->5","7"]
 * 思路：遍历，当 nums[i]!=nums[i-1]+1 时结束上一个区间；循环结束后处理最后一个区间。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function summaryRanges(nums: number[]): string[] {
    const result: string[] = [];
    const n = nums.length;
    if (n === 0) return result;

    let start = nums[0];

    for (let i = 1; i < n; i++) {
        if (nums[i] !== nums[i - 1] + 1) {
            result.push(start === nums[i - 1] ? `${start}` : `${start}->${nums[i - 1]}`);
            start = nums[i];
        }
    }

    result.push(start === nums[n - 1] ? `${start}` : `${start}->${nums[n - 1]}`);
    return result;
}
export { summaryRanges };
