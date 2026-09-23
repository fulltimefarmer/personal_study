import heapq
import random
from typing import List


def findKthLargest(nums: List[int], k: int) -> int:
    """堆解法：O(n log k)。"""
    heap = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]


def findKthLargest_quickselect(nums: List[int], k: int) -> int:
    """快速选择：平均 O(n)。"""
    target = len(nums) - k

    def partition(lo: int, hi: int) -> int:
        pivot = nums[hi]
        i = lo
        for j in range(lo, hi):
            if nums[j] <= pivot:
                nums[i], nums[j] = nums[j], nums[i]
                i += 1
        nums[i], nums[hi] = nums[hi], nums[i]
        return i

    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        p = random.randint(lo, hi)
        nums[p], nums[hi] = nums[hi], nums[p]
        idx = partition(lo, hi)
        if idx == target:
            return nums[idx]
        if idx < target:
            lo = idx + 1
        else:
            hi = idx - 1
    return -1


if __name__ == "__main__":
    assert findKthLargest([3, 2, 1, 5, 6, 4], 2) == 5
    assert findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert findKthLargest_quickselect([3, 2, 1, 5, 6, 4], 2) == 5
    assert findKthLargest_quickselect([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    print("all tests passed")
