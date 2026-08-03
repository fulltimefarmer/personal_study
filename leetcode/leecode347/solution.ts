/**
 * 考点：数组、哈希表、桶排序
 * 题目：Top K Frequent Elements（前K个高频元素）
 * 题目描述：返回数组中出现频率前 k 高的元素
 * 思路：桶排序。先统计频率，再以频率为下标分桶，
 *       从高频到低频遍历收集 k 个元素。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */
function topKFrequent(nums: number[], k: number): number[] {
    const freq = new Map<number, number>();
    for (const num of nums) {
        freq.set(num, (freq.get(num) || 0) + 1);
    }

    const buckets: number[][] = new Array(nums.length + 1);
    for (let i = 0; i <= nums.length; i++) {
        buckets[i] = [];
    }

    for (const [num, count] of freq) {
        buckets[count].push(num);
    }

    const result: number[] = [];
    for (let i = buckets.length - 1; i >= 0 && result.length < k; i--) {
        for (const num of buckets[i]) {
            result.push(num);
            if (result.length === k) break;
        }
    }

    return result;
}

export { topKFrequent };
