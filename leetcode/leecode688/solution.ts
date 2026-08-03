/**
 * 考点：动态规划
 * 题目：Knight Probability in Chessboard（骑士在棋盘上的概率）
 * 题目描述：骑士从 (row,column) 开始，每次随机走 8 个方向之一，走 k 步。求 k 步后仍在棋盘上的概率。
 * 示例：
 *   输入: n=3, k=2, row=0, column=0 → 输出: 0.0625
 * 思路：DP。dp[step][r][c] 表示 step 步后在 (r,c) 的概率。dp[step+1][nr][nc] += dp[step][r][c]/8。最终求和。
 * 时间复杂度：O(k * n²)
 * 空间复杂度：O(n²)
 */
function knightProbability(n: number, k: number, row: number, column: number): number {
    const directions = [[-2,-1],[-2,1],[-1,-2],[-1,2],[1,-2],[1,2],[2,-1],[2,1]];

    let dp: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
    dp[row][column] = 1;

    for (let step = 0; step < k; step++) {
        const next: number[][] = Array.from({ length: n }, () => new Array(n).fill(0));
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < n; c++) {
                if (dp[r][c] === 0) continue;
                for (const [dr, dc] of directions) {
                    const nr = r + dr;
                    const nc = c + dc;
                    if (nr >= 0 && nr < n && nc >= 0 && nc < n) {
                        next[nr][nc] += dp[r][c] / 8;
                    }
                }
            }
        }
        dp = next;
    }

    let probability = 0;
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            probability += dp[r][c];
        }
    }

    return probability;
}

export { knightProbability };
