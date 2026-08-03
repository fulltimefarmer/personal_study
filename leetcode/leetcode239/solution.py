"""
考点：队列、数组、滑动窗口、单调队列
题目：Sliding Window Maximum（滑动窗口最大值）
题目描述：给定数组 nums 和窗口大小 k，返回每个滑动窗口中的最大值。
  示例：nums = [1,3,-1,-3,5,3,6,7], k = 3 → [3,3,5,5,6,7]
思路：单调递减双端队列（deque）。队列中存储索引，对应的值单调递减。
  当窗口滑动时：
  1. 移除超出窗口的索引（队头）
  2. 移除比当前元素小的索引（队尾，因为它们不可能是后续窗口的最大值）
  3. 将当前索引加入队尾
  4. 窗口形成后将队头值加入结果
时间复杂度：O(n)
空间复杂度：O(k)
"""

from collections import deque


def maxSlidingWindow(nums: list[int], k: int) -> list[int]:
    result: list[int] = []
    # 双端队列存储索引，对应的 nums 值保持单调递减（队头最大）
    dq: deque[int] = deque()

    for i in range(len(nums)):
        # 移除不在当前窗口范围内的索引（窗口范围：[i-k+1, i]）
        # dq[0] 是队头，如果它等于 i - k，说明已经滑出窗口
        if dq and dq[0] == i - k:
            dq.popleft()

        # 维护单调递减：移除队尾所有比当前元素小的索引
        # 因为只要当前元素在窗口中，那些更小且更早的元素就永远不会成为最大值
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()

        dq.append(i)  # 当前索引入队

        # 窗口形成后（i >= k-1），队头就是当前窗口的最大值
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result


if __name__ == "__main__":
    assert maxSlidingWindow([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert maxSlidingWindow([1], 1) == [1]
    assert maxSlidingWindow([1, -1], 1) == [1, -1]
    assert maxSlidingWindow([9, 11], 2) == [11]
