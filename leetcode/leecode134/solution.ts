/**
 * 考点：Greedy, Array
 * 题目：Gas Station（加油站）
 * 题目描述：环形加油站，找到能绕行一周的起点，不存在返回 -1，存在则解唯一。
 * 示例 1：gas=[1,2,3,4,5], cost=[3,4,5,1,2]，输出 3
 * 示例 2：gas=[2,3,4], cost=[3,4,3]，输出 -1
 * 思路：总油量 < 总消耗则返回 -1。遍历维护 tank，tank<0 时重置起点和 tank。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
function canCompleteCircuit(gas: number[], cost: number[]): number {
    let totalGas = 0;
    let totalCost = 0;
    let tank = 0;
    let start = 0;

    for (let i = 0; i < gas.length; i++) {
        totalGas += gas[i];
        totalCost += cost[i];
        tank += gas[i] - cost[i];

        if (tank < 0) {
            start = i + 1;
            tank = 0;
        }
    }

    return totalGas >= totalCost ? start : -1;
}

export { canCompleteCircuit };
