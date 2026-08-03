/**
 * 考点：数组、数学、动态规划、排序
 * 题目：Largest Divisible Subset（最大整除子集）
 * 题目描述：在无重复正整数集合中找出最大整除子集，任意两数相互整除
 * 思路：排序后 DP。dp[i] 为以 nums[i] 结尾的最大子集大小，
 *       prev[i] 记录前驱用于回溯构建结果。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n)
 */
function largestDivisibleSubset(nums: number[]): number[] {
    const n = nums.length;
    if (n === 0) return [];

    nums.sort((a, b) => a - b);

    const dp = new Array(n).fill(1);
    const prev = new Array(n).fill(-1);

    let maxIndex = 0;

    for (let i = 1; i < n; i++) {
        for (let j = 0; j < i; j++) {
            if (nums[i] % nums[j] === 0 && dp[j] + 1 > dp[i]) {
                dp[i] = dp[j] + 1;
                prev[i] = j;
            }
        }
        if (dp[i] > dp[maxIndex]) {
            maxIndex = i;
        }
    }

    const result: number[] = [];
    let cur: number = maxIndex;
    while (cur !== -1) {
        result.push(nums[cur]);
        cur = prev[cur];
    }

    return result.reverse();
}

export { largestDivisibleSubset };
