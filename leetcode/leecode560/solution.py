"""
考点：数组, 哈希表, 前缀和
题目：Subarray Sum Equals K（和为K的子数组）
题目描述：给定整数数组 nums 和整数 k，统计和为 k 的连续子数组的个数。
思路：前缀和+哈希表。prefixSum[j] - k = prefixSum[i-1]，遍历时用字典记录前缀和出现次数，查找 prefixSum-k 的个数累加。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def subarraySum(nums: list[int], k: int) -> int:
    # prefix_map 记录前缀和出现的次数
    # key: 前缀和的值, value: 该前缀和出现的次数
    prefix_map: dict[int, int] = {0: 1}  # 前缀和为 0 出现 1 次（空前缀，处理从头开始的子数组）

    count = 0
    prefix_sum = 0

    for num in nums:
        prefix_sum += num

        # 如果存在前缀和 prefix_sum - k，说明从该前缀和之后到当前位置的子数组和为 k
        # prefix_sum(当前) - prefix_sum(之前) = k → prefix_sum(之前) = prefix_sum - k
        target = prefix_sum - k
        count += prefix_map.get(target, 0)

        # 将当前前缀和记录到字典中
        prefix_map[prefix_sum] = prefix_map.get(prefix_sum, 0) + 1

    return count


if __name__ == "__main__":
    # 示例：nums=[1,1,1], k=2 → 输出: 2（子数组 [1,1] 出现两次：索引 [0,1] 和 [1,2]）
    assert subarraySum([1, 1, 1], 2) == 2
    # 示例：nums=[1,2,3], k=3 → 输出: 2（[1,2] 和 [3]）
    assert subarraySum([1, 2, 3], 3) == 2
