/**
 * 考点：数学, 二分搜索, 动态规划
 * 题目：Super Egg Drop（鸡蛋掉落）
 * 题目描述：k 个鸡蛋，n 层楼。找到临界楼层 f，鸡蛋在 f 层及以上会碎。求最坏情况下确定 f 所需的最小操作次数。
 * 示例：
 *   输入: k=1, n=2 → 输出: 2
 *   输入: k=2, n=6 → 输出: 3
 * 思路：DP 基于移动次数的思维。dp[m][k] 表示 m 次移动、k 个鸡蛋可确定的最大楼层数。dp[m][k]=dp[m-1][k-1]+dp[m-1][k]+1。增加 m 直到 dp[m][k]>=n。
 * 时间复杂度：O(k * m)
 * 空间复杂度：O(k)
 */
function superEggDrop(k: number, n: number): number {
    const dp: number[] = new Array(k + 1).fill(0);
    let m = 0;

    while (dp[k] < n) {
        m++;
        for (let i = k; i >= 1; i--) {
            dp[i] = dp[i] + dp[i - 1] + 1;
        }
    }

    return m;
}

export { superEggDrop };
