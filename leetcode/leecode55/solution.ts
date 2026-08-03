/**
 * 考点：Greedy, Array, Dynamic Programming
 * 题目：Jump Game（跳跃游戏）
 * 题目描述：给定非负整数数组 nums，最初位于第一个下标，每个元素代表可跳跃的最大长度，判断是否能到达最后一个下标。
 * 示例：nums = [2,3,1,1,4] → true
 * 示例：nums = [3,2,1,0,4] → false
 * 思路：贪心算法。维护 maxReach 表示当前能到达的最远距离，遍历时若 i > maxReach 则不可达，
 *       不断更新 maxReach，一旦 >= n-1 即可返回 true。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function canJump(nums: number[]): boolean {
    let maxReach = 0;

    for (let i = 0; i < nums.length; i++) {
        if (i > maxReach) return false;
        maxReach = Math.max(maxReach, i + nums[i]);
        if (maxReach >= nums.length - 1) return true;
    }

    return true;
}

export { canJump };
