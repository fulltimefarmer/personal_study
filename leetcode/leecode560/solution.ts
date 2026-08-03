/**
 * 考点：数组, 哈希表, 前缀和
 * 题目：Subarray Sum Equals K（和为K的子数组）
 * 题目描述：给定整数数组 nums 和整数 k，统计和为 k 的连续子数组的个数。
 * 示例：
 *   输入: nums=[1,1,1], k=2 → 输出: 2
 *   输入: nums=[1,2,3], k=3 → 输出: 2
 * 思路：前缀和+哈希表。prefixSum[j]-k=prefixSum[i-1]，遍历时用 map 记录前缀和出现次数，查找 prefixSum-k 的个数累加。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function subarraySum(nums: number[], k: number): number {
    const map = new Map<number, number>();
    map.set(0, 1);

    let count = 0;
    let prefixSum = 0;

    for (const num of nums) {
        prefixSum += num;

        const target = prefixSum - k;
        if (map.has(target)) {
            count += map.get(target)!;
        }

        map.set(prefixSum, (map.get(prefixSum) || 0) + 1);
    }

    return count;
}

export { subarraySum };
