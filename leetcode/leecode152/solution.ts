/**
 * 考点：Array, Dynamic Programming
 * 题目：Maximum Product Subarray（乘积最大子数组）
 * 题目描述：找出数组中乘积最大的连续子数组。
 * 示例 1：[2,3,-2,4]，输出 6（子数组 [2,3]）
 * 示例 2：[-2,0,-1]，输出 0
 * 思路：DP，同时维护最大乘积和最小乘积（负负得正）。curMax = max(num, maxDp*num, minDp*num)。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function maxProduct(nums: number[]): number {
    let maxDp = nums[0];
    let minDp = nums[0];
    let result = nums[0];

    for (let i = 1; i < nums.length; i++) {
        const num = nums[i];
        const prevMax = maxDp;
        const prevMin = minDp;
        maxDp = Math.max(num, prevMax * num, prevMin * num);
        minDp = Math.min(num, prevMax * num, prevMin * num);
        result = Math.max(result, maxDp);
    }

    return result;
}

export { maxProduct };
