"""
考点：Greedy, Array
题目：Gas Station（加油站）
题目描述：环形加油站，找到能绕行一周的起点，不存在返回 -1，存在则解唯一。
示例 1：gas=[1,2,3,4,5], cost=[3,4,5,1,2]，输出 3
示例 2：gas=[2,3,4], cost=[3,4,3]，输出 -1
思路：总油量 < 总消耗则返回 -1。遍历维护 tank，tank<0 时重置起点和 tank。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def canCompleteCircuit(gas: list[int], cost: list[int]) -> int:
    total_gas: int = 0   # 总油量
    total_cost: int = 0  # 总消耗
    tank: int = 0        # 当前油箱剩余油量
    start: int = 0       # 起点索引

    for i in range(len(gas)):
        total_gas += gas[i]
        total_cost += cost[i]
        tank += gas[i] - cost[i]

        # 如果油箱为负，说明从 start 到 i 之间的任何站都无法作为起点
        # 因为到达 i 时油不够了，必须从 i+1 重新开始
        if tank < 0:
            start = i + 1
            tank = 0    # 重置油箱，从新起点重新计算

    # 总油量 >= 总消耗，才可能存在解（且解唯一）
    return start if total_gas >= total_cost else -1


if __name__ == "__main__":
    assert canCompleteCircuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert canCompleteCircuit([2, 3, 4], [3, 4, 3]) == -1
    assert canCompleteCircuit([5, 1, 2, 3, 4], [4, 4, 1, 5, 1]) == 4
