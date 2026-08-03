/**
 * 考点：数组, 数学, 动态规划, 博弈论
 * 题目：Stone Game（石子游戏）
 * 题目描述：偶数堆石子排成一行，Alice 和 Bob 轮流从两端取整堆，取完比大小。Alice 先手，双方最优策略。判断 Alice 是否能赢。
 * 示例：
 *   输入: [5,3,4,5] → 输出: true
 * 思路：数学结论。偶数堆+奇数总石子数 => Alice 可以控制拿全部偶数索引或奇数索引，二者和不相等，Alice 必赢。直接返回 true。（DP解法：dp[i][j]=max(piles[i]-dp[i+1][j], piles[j]-dp[i][j-1])，dp[0][n-1]>0则赢）
 * 时间复杂度：O(1)（数学法）/ O(n²)（DP法）
 * 空间复杂度：O(1) / O(n²)
 */
function stoneGame(piles: number[]): boolean {
    return true;
}

export { stoneGame };
