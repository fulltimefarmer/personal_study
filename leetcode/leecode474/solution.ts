/**
 * 考点：数组, 字符串, 动态规划
 * 题目：Ones and Zeroes（一和零）
 * 题目描述：给定二进制字符串数组 strs 和两个整数 m 和 n。找出 strs 的最大子集的大小，该子集中最多有 m 个 0 和 n 个 1。
 * 示例：
 *   输入: strs=["10","0001","111001","1","0"], m=5, n=3 → 输出: 4
 * 思路：二维 0-1 背包。dp[j][k] 表示使用 j 个 0 和 k 个 1 时最多可选的字符串数。对每个字符串统计 0 和 1 的数量，倒序更新 dp。
 * 时间复杂度：O(L * m * n)
 * 空间复杂度：O(m * n)
 */
function findMaxForm(strs: string[], m: number, n: number): number {
    const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

    for (const s of strs) {
        let zeros = 0;
        let ones = 0;
        for (const ch of s) {
            if (ch === '0') zeros++;
            else ones++;
        }

        for (let j = m; j >= zeros; j--) {
            for (let k = n; k >= ones; k--) {
                dp[j][k] = Math.max(dp[j][k], dp[j - zeros][k - ones] + 1);
            }
        }
    }

    return dp[m][n];
}

export { findMaxForm };
