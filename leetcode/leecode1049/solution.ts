/**
 * 考点：数组, 动态规划
 * 题目：Last Stone Weight II（最后一块石头的重量II）
 * 题目描述：stones[i] 表示石头重量。每次取两块粉碎，x<=y 时 x 粉碎、y 变 y-x。求最后剩下石头的最小重量。
 * 示例：
 *   输入: [2,7,4,1,8,1] → 输出: 1
 * 思路：转为 0-1 背包。将石头分成两堆，使重量差最小。选子集使其和尽量接近 sum/2。dp[j] 表示能选出和 j 的子集，倒序更新。
 * 时间复杂度：O(n * sum/2)
 * 空间复杂度：O(sum/2)
 */
function lastStoneWeightII(stones: number[]): number {
    const sum = stones.reduce((a, b) => a + b, 0);
    const target = Math.floor(sum / 2);
    const dp: boolean[] = new Array(target + 1).fill(false);
    dp[0] = true;

    for (const stone of stones) {
        for (let j = target; j >= stone; j--) {
            dp[j] = dp[j] || dp[j - stone];
        }
    }

    for (let j = target; j >= 0; j--) {
        if (dp[j]) {
            return sum - 2 * j;
        }
    }

    return 0;
}

export { lastStoneWeightII };
