/**
 * 考点：Dynamic Programming
 * 题目：Edit Distance
 * 题目描述：给你两个单词 word1 和 word2，请你计算将 word1 转换成 word2 所使用的最少操作数。
 *          你可以对一个单词进行如下三种操作：
 *          - 插入一个字符
 *          - 删除一个字符
 *          - 替换一个字符
 *          示例：输入 word1 = "horse"，word2 = "ros"，输出 3。
 *          解释：horse -> rorse（替换 'h' 为 'r'）-> rose（删除 'r'）-> ros（删除 'e'）。
 * 思路：第一步：定义 dp[i][j] 表示 word1 前 i 个字符转换为 word2 前 j 个字符的最少操作数。
 *       第二步：初始化边界：
 *              - dp[0][j] = j，表示将空串转换为 word2 前 j 个字符需要插入 j 次。
 *              - dp[i][0] = i，表示将 word1 前 i 个字符转换为空串需要删除 i 次。
 *       第三步：使用一维数组 dp[j] 滚动优化，初始 dp[j] = j。
 *       第四步：外层遍历 word1 的每个字符 i = 1..m，用 prev 保存左上角的 dp[i-1][j-1]，
 *              并更新 dp[0] = i。
 *       第五步：内层遍历 word2 的每个字符 j = 1..n：
 *              - 若 word1[i-1] == word2[j-1]，则 dp[j] = prev（无需新操作）。
 *              - 否则 dp[j] = 1 + min(dp[j]（删除）, dp[j-1]（插入）, prev（替换）)。
 *              - 更新 prev 为更新前的 dp[j]，供下一轮使用。
 *       第六步：返回 dp[n]，即最少操作数。
 * 算法：动态规划（二维 DP，可优化为一维滚动数组）。
 * 时间复杂度：O(m * n)
 * 空间复杂度：O(n)，使用一维数组
 */
function minDistance(word1: string, word2: string): number {
    const m = word1.length, n = word2.length;
    const dp: number[] = new Array(n + 1).fill(0);
    for (let j = 0; j <= n; j++) {
        dp[j] = j;
    }
    for (let i = 1; i <= m; i++) {
        let prev = dp[0];
        dp[0] = i;
        for (let j = 1; j <= n; j++) {
            const temp = dp[j];
            if (word1[i - 1] === word2[j - 1]) {
                dp[j] = prev;
            } else {
                dp[j] = 1 + Math.min(dp[j], dp[j - 1], prev);
            }
            prev = temp;
        }
    }
    return dp[n];
}
