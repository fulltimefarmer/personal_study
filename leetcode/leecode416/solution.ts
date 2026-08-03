/**
 * 考点：数组、动态规划（0-1 背包）
 * 题目：Partition Equal Subset Sum（分割等和子集）
 * 题目描述：判断能否将数组分成两个和相等的子集
 * 思路：0-1 背包。总和的奇偶快速判断，target = sum/2。
 *       dp[i] = dp[i] || dp[i - num]，从 target 到 num 逆向遍历防止重复使用。
 * 时间复杂度：O(n × sum)
 * 空间复杂度：O(sum)
 */
function canPartition(nums: number[]): boolean {
    const sum = nums.reduce((a, b) => a + b, 0);
    if (sum % 2 !== 0) return false;

    const target = sum / 2;
    const dp = new Array(target + 1).fill(false);
    dp[0] = true;

    for (const num of nums) {
        for (let i = target; i >= num; i--) {
            dp[i] = dp[i] || dp[i - num];
        }
    }

    return dp[target];
}

export { canPartition };
