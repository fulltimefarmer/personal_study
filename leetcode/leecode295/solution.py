"""
考点：设计、堆（优先队列）、数据流
题目：Find Median from Data Stream（数据流的中位数）—— LeetCode 295
题目描述：设计数据结构支持动态插入和查询中位数
思路：双堆法。最大堆存较小的一半，最小堆存较大的一半。
      保持平衡：maxHeap.size >= minHeap.size 且差值 <= 1。
      中位数：相等取两堆顶平均，否则取 maxHeap 堆顶。
时间复杂度：O(log n) 插入, O(1) 查询
空间复杂度：O(n)
"""

import heapq


class MedianFinder:
    """数据流中位数查找器，使用双堆（最大堆 + 最小堆）维护数据"""

    def __init__(self) -> None:
        # max_heap：存储较小的一半数据，Python heapq 是最小堆，通过取负数模拟最大堆
        # 例如存入 5，实际存 -5，堆顶（最小值）-5 对应的实际值就是最大值 5
        self.max_heap: list[int] = []
        # min_heap：存储较大的一半数据，直接使用最小堆
        self.min_heap: list[int] = []

    def addNum(self, num: int) -> None:
        # 策略：新数字先放入 max_heap，再把 max_heap 的最大值移到 min_heap
        # Python 的 heapq.heappush 和 heapq.heappop 操作的都是列表元素的直接值
        # 对 max_heap 使用的负值技巧：push 时取负，pop 后取负恢复原值
        heapq.heappush(self.max_heap, -num)
        # 将 max_heap 中最大的元素（即堆顶的负数恢复后）移入 min_heap
        heapq.heappush(self.min_heap, -heapq.heappop(self.max_heap))

        # 保持平衡：max_heap 的大小 >= min_heap 的大小
        # 如果 min_heap 更大，把 min_heap 的最小值移回 max_heap
        if len(self.min_heap) > len(self.max_heap):
            heapq.heappush(self.max_heap, -heapq.heappop(self.min_heap))

    def findMedian(self) -> float:
        # 如果 max_heap 更大，说明奇数个元素，中位数就是 max_heap 的堆顶
        if len(self.max_heap) > len(self.min_heap):
            return float(-self.max_heap[0])  # 取负恢复原值
        # 如果大小相等，偶数个元素，中位数为两堆顶的平均值
        return (-self.max_heap[0] + self.min_heap[0]) / 2


if __name__ == "__main__":
    mf = MedianFinder()
    mf.addNum(1)
    mf.addNum(2)
    assert mf.findMedian() == 1.5
    mf.addNum(3)
    assert mf.findMedian() == 2.0

    mf2 = MedianFinder()
    mf2.addNum(-1)
    assert mf2.findMedian() == -1.0
    mf2.addNum(-2)
    assert mf2.findMedian() == -1.5
    mf2.addNum(-3)
    assert mf2.findMedian() == -2.0

    print("所有断言通过！")
