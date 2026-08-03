/**
 * 考点：Greedy, Array, Dynamic Programming
 * 题目：Jump Game II（跳跃游戏 II）
 * 题目描述：每个元素表示从该位置可跳的最大长度，返回到达最后一个位置的最小跳跃次数。
 * 示例：nums = [2,3,1,1,4] => 2
 * 思路：贪心，每步在可达范围内选能跳最远的位置，到达当前边界时跳跃次数+1
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function jump(nums: number[]): number {
    if (nums.length <= 1) return 0;

    let jumps = 0;
    let currentEnd = 0;
    let farthest = 0;

    for (let i = 0; i < nums.length - 1; i++) {
        farthest = Math.max(farthest, i + nums[i]);

        if (i === currentEnd) {
            jumps++;
            currentEnd = farthest;
        }
    }

    return jumps;
}
export { jump };
