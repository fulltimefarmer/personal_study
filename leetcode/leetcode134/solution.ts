/**
 * 考点：贪心、数组
 * 题目：Gas Station（加油站）
 * 题目描述：环形路线上有 n 个加油站，gas[i] 是油量，cost[i] 是消耗，求能绕行一周的起点。
 *   示例：gas = [1,2,3,4,5], cost = [3,4,5,1,2] → 3
 * 思路：贪心。若总油量 < 总消耗则一定不行；否则当前段油量变负时跳过该段，重置起点。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

function canCompleteCircuit(gas: number[], cost: number[]): number {
  let totalTank = 0;
  let currTank = 0;
  let start = 0;

  for (let i = 0; i < gas.length; i++) {
    const diff = gas[i] - cost[i];
    totalTank += diff;
    currTank += diff;

    if (currTank < 0) {
      start = i + 1;
      currTank = 0;
    }
  }

  return totalTank >= 0 ? start : -1;
}

export { canCompleteCircuit };
