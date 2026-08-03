"""
考点：数组、哈希表、桶排序
题目：Top K Frequent Elements（前K个高频元素）—— LeetCode 347
题目描述：返回数组中出现频率前 k 高的元素
思路：桶排序。先统计频率，再以频率为下标分桶，
      从高频到低频遍历收集 k 个元素。
时间复杂度：O(n)
空间复杂度：O(n)
"""

from collections import Counter


def topKFrequent(nums: list[int], k: int) -> list[int]:
    # collections.Counter 是一个字典子类，自动统计元素出现次数
    # 例如 Counter([1,1,2,2,2,3]) → Counter({2: 3, 1: 2, 3: 1})
    freq = Counter(nums)

    # 桶排序：buckets[i] 存出现次数为 i 的所有元素
    # 大小为 n+1，因为最多出现 n 次（n 为数组长度）
    n = len(nums)
    buckets: list[list[int]] = [[] for _ in range(n + 1)]

    # 将元素按频率放入对应桶中
    for num, count in freq.items():
        buckets[count].append(num)

    result: list[int] = []
    # 从高频到低频（从 n 到 0）遍历桶，收集 k 个元素
    for i in range(n, -1, -1):
        for num in buckets[i]:
            result.append(num)
            if len(result) == k:
                return result

    return result  # 理论上不会执行到这里


if __name__ == "__main__":
    assert sorted(topKFrequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert topKFrequent([1], 1) == [1]
    assert sorted(topKFrequent([1, 2], 2)) == [1, 2]
    assert sorted(topKFrequent([3, 0, 1, 0], 1)) == [0]
    assert sorted(topKFrequent([4, 1, -1, 2, -1, 2, 3], 2)) == [-1, 2]
    print("所有断言通过！")
