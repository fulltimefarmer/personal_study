/**
 * 考点：Greedy, Array, Dynamic Programming
 * 题目：Jump Game II（跳跃游戏 II）
 * 题目描述：求到达数组末尾的最少跳跃次数。如 [2,3,1,1,4] → 2
 * 思路：贪心，维护当前跳跃可达边界curEnd和全局最远curFarthest。到达curEnd时jumps++并更新边界。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function jump(nums: number[]): number {
    let jumps = 0;
    let curEnd = 0;
    let curFarthest = 0;

    for (let i = 0; i < nums.length - 1; i++) {
        curFarthest = Math.max(curFarthest, i + nums[i]);
        if (i === curEnd) {
            jumps++;
            curEnd = curFarthest;
            if (curEnd >= nums.length - 1) break;
        }
    }

    return jumps;
}

export { jump };
