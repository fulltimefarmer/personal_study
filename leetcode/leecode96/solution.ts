/**
 * 考点：Tree, BST, Math, Dynamic Programming, Binary Tree
 * 题目：Unique Binary Search Trees（不同的二叉搜索树）
 * 题目描述：给定 n 个节点，节点值为 1..n，求能构成的不同二叉搜索树种数。
 * 示例：n = 3 → 5
 * 思路：动态规划（卡特兰数）。dp[i] = Σ dp[j-1] * dp[i-j]，j 作为根节点。
 *       dp[0] = 1 表示空树。
 * 时间复杂度：O(n^2)
 * 空间复杂度：O(n)
 */
function numTrees(n: number): number {
    const dp: number[] = new Array(n + 1).fill(0);
    dp[0] = 1;
    dp[1] = 1;

    for (let i = 2; i <= n; i++) {
        for (let j = 1; j <= i; j++) {
            dp[i] += dp[j - 1] * dp[i - j];
        }
    }

    return dp[n];
}

export { numTrees };
