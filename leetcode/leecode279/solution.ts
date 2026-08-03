/**
 * 考点：BFS、数学、动态规划
 * 题目：Perfect Squares（完全平方数）
 * 题目描述：给定整数 n，求最少需要多少个完全平方数相加得到 n
 * 思路：动态规划。dp[i] = min(dp[i - j*j] + 1)，其中 j*j <= i。
 * 时间复杂度：O(n * sqrt(n))
 * 空间复杂度：O(n)
 */
function numSquares(n: number): number {
    const dp = new Array(n + 1).fill(Infinity);
    dp[0] = 0;

    const squares: number[] = [];
    for (let j = 1; j * j <= n; j++) {
        squares.push(j * j);
    }

    for (let i = 1; i <= n; i++) {
        for (const square of squares) {
            if (square > i) break;
            dp[i] = Math.min(dp[i], dp[i - square] + 1);
        }
    }

    return dp[n];
}

export { numSquares };
