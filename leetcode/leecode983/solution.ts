/**
 * 考点：数组, 动态规划
 * 题目：Minimum Cost For Tickets（最低票价）
 * 题目描述：旅行日数组 days，三种票：1天/7天/30天，对应票价 costs[0]/costs[1]/costs[2]。求覆盖所有旅行日的最低花费。
 * 示例：
 *   输入: days=[1,4,6,7,8,20], costs=[2,7,15] → 输出: 11
 * 思路：DP。dp[i] 表示到第 i 天的最小花费。非旅行日 dp[i]=dp[i-1]；旅行日 dp[i]=min(dp[i-1]+c0, dp[max(0,i-7)]+c1, dp[max(0,i-30)]+c2)。
 * 时间复杂度：O(365)
 * 空间复杂度：O(365)
 */
function mincostTickets(days: number[], costs: number[]): number {
    const daySet = new Set(days);
    const lastDay = days[days.length - 1];
    const dp: number[] = new Array(lastDay + 1).fill(0);

    for (let i = 1; i <= lastDay; i++) {
        if (!daySet.has(i)) {
            dp[i] = dp[i - 1];
        } else {
            dp[i] = Math.min(
                dp[i - 1] + costs[0],
                dp[Math.max(0, i - 7)] + costs[1],
                dp[Math.max(0, i - 30)] + costs[2]
            );
        }
    }

    return dp[lastDay];
}

export { mincostTickets };
