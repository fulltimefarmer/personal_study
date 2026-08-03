/**
 * 考点：递归, 数组, 数学, 动态规划, 博弈论
 * 题目：Predict the Winner（预测赢家）
 * 题目描述：给定 nums，玩家 1 和玩家 2 轮流从数组两端取数，分数加到各自总分。双方都采取最优策略，判断玩家 1 是否能赢（平局也算赢）。
 * 示例：
 *   输入: [1,5,2] → 输出: false
 *   输入: [1,5,233,7] → 输出: true
 * 思路：博弈 DP。dp[i][j] 表示 nums[i..j] 中当前先手的最大净胜分。dp[i][j] = max(nums[i]-dp[i+1][j], nums[j]-dp[i][j-1])。最终 dp[0][n-1]>=0 则玩家1赢。
 * 时间复杂度：O(n²)
 * 空间复杂度：O(n²)
 */
function predictTheWinner(nums: number[]): boolean {
    const n = nums.length;
    const dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));

    for (let i = 0; i < n; i++) {
        dp[i][i] = nums[i];
    }

    for (let len = 2; len <= n; len++) {
        for (let i = 0; i + len - 1 < n; i++) {
            const j = i + len - 1;
            dp[i][j] = Math.max(nums[i] - dp[i + 1][j], nums[j] - dp[i][j - 1]);
        }
    }

    return dp[0][n - 1] >= 0;
}

export { predictTheWinner };
