/**
 * 考点：数组, 哈希表, 动态规划
 * 题目：Delete and Earn（删除并获得点数）
 * 题目描述：每次选择 nums[i] 获得 nums[i] 点数，但必须删除所有 nums[i]-1 和 nums[i]+1。求最大点数。
 * 示例：
 *   输入: [3,4,2] → 输出: 6
 *   输入: [2,2,3,3,3,4] → 输出: 9
 * 思路：转化为打家劫舍。统计每个值出现的总点数，points[val]=val*count。问题变为在 points 数组中不能取相邻元素的最大和。dp[i]=max(dp[i-1], dp[i-2]+points[i])。
 * 时间复杂度：O(N + maxVal)
 * 空间复杂度：O(maxVal)
 */
function deleteAndEarn(nums: number[]): number {
    let maxVal = 0;
    for (const num of nums) {
        maxVal = Math.max(maxVal, num);
    }

    const points: number[] = new Array(maxVal + 1).fill(0);
    for (const num of nums) {
        points[num] += num;
    }

    let prev2 = 0;
    let prev1 = points[0];

    for (let i = 1; i <= maxVal; i++) {
        const curr = Math.max(prev1, prev2 + points[i]);
        prev2 = prev1;
        prev1 = curr;
    }

    return prev1;
}

export { deleteAndEarn };
