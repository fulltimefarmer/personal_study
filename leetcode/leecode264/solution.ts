/**
 * 考点：数学、动态规划（三指针）
 * 题目：Ugly Number II（丑数II）
 * 题目描述：找出第 n 个只包含质因数 2、3、5 的丑数
 * 思路：动态规划 + 三指针。dp[i] 是第 i 个丑数，p2/p3/p5 分别指向
 *       下一个将要乘以 2/3/5 的丑数位置，每次取最小值并移动对应指针。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function nthUglyNumber(n: number): number {
    const dp: number[] = new Array(n + 1);
    dp[1] = 1;

    let p2 = 1, p3 = 1, p5 = 1;

    for (let i = 2; i <= n; i++) {
        const num2 = dp[p2] * 2;
        const num3 = dp[p3] * 3;
        const num5 = dp[p5] * 5;

        dp[i] = Math.min(num2, num3, num5);

        if (dp[i] === num2) p2++;
        if (dp[i] === num3) p3++;
        if (dp[i] === num5) p5++;
    }

    return dp[n];
}

export { nthUglyNumber };
