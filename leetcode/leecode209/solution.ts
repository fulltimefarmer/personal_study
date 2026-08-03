/**
 * 考点：数组、二分查找、前缀和、滑动窗口
 * 题目：Minimum Size Subarray Sum（长度最小的子数组）
 * 题目描述：找出和≥target的最短连续子数组长度。target=7,nums=[2,3,1,2,4,3] 输出 2（子数组[4,3]）
 * 思路：滑动窗口。右指针扩展累加 sum，当 sum>=target 时收缩左指针找最短长度。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function minSubArrayLen(target: number, nums: number[]): number {
    let left = 0;
    let sum = 0;
    let minLen = Infinity;

    for (let right = 0; right < nums.length; right++) {
        sum += nums[right];

        while (sum >= target) {
            minLen = Math.min(minLen, right - left + 1);
            sum -= nums[left];
            left++;
        }
    }

    return minLen === Infinity ? 0 : minLen;
}
export { minSubArrayLen };
