"""
考点：贪心、堆（优先队列）
题目：Meeting Rooms II（会议室II）—— LeetCode 253
题目描述：给定会议时间区间数组，求所需最少会议室数量
思路：按开始时间排序，用最小堆跟踪会议结束时间。每次新会议开始时，
      释放已结束的会议室（弹出堆顶），堆的大小就是所需会议室数。
时间复杂度：O(n log n)
空间复杂度：O(n)
"""

import heapq


def minMeetingRooms(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0

    # 按会议开始时间升序排序
    intervals.sort(key=lambda x: x[0])

    # 最小堆：存储正在进行的会议的结束时间
    heap: list[int] = []

    for start, end in intervals:
        # 如果堆不为空且最早结束的会议已经结束（结束时间 <= 当前开始时间），释放会议室
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        # 将当前会议的结束时间加入堆中，堆的大小就是当前需要的会议室数
        heapq.heappush(heap, end)

    # heapq 是最小堆，堆顶是最小值（最早结束时间）
    return len(heap)


if __name__ == "__main__":
    # 示例1：需要2个会议室，因为[0,30]和[5,10]重叠
    assert minMeetingRooms([[0, 30], [5, 10], [15, 20]]) == 2
    # 示例2：没有重叠，只需要1个会议室
    assert minMeetingRooms([[7, 10], [2, 4]]) == 1
    # 边界测试：空数组
    assert minMeetingRooms([]) == 0
    # 边界测试：单个会议
    assert minMeetingRooms([[1, 5]]) == 1
    print("所有断言通过！")
