"""
考点：队列、数组、滑动窗口、单调队列、堆
题目：Sliding Window Maximum（滑动窗口最大值）
思路：单调递减双端队列存索引。移除过期索引；移除队尾所有小于当前值的索引；
      队首即为当前窗口最大值。
时间复杂度：O(n)
空间复杂度：O(k)
"""

from collections import deque


def maxSlidingWindow(nums: list[int], k: int) -> list[int]:
    n = len(nums)
    result: list[int] = [0] * (n - k + 1)
    # 双端队列 stores 索引，保持单调递减（队首始终是当前窗口最大值索引）
    # 使用 Python 的 collections.deque 实现 O(1) 两端操作
    dq: deque[int] = deque()
    idx = 0  # 结果数组的写入位置

    for i in range(n):
        # 移除已经滑出窗口的索引（队首索引 <= i-k 即为过期）
        while dq and dq[0] <= i - k:
            dq.popleft()  # deque.popleft() 是 O(1)

        # 维护单调递减：移除队尾所有值小于当前值的索引
        # 因为这些值在后续窗口中不可能是最大值
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()  # deque.pop() 是 O(1)

        dq.append(i)  # 将当前索引加入队尾

        # 当窗口形成后（i >= k-1），记录窗口最大值
        if i >= k - 1:
            result[idx] = nums[dq[0]]  # 队首索引对应的值即为最大值
            idx += 1

    return result


if __name__ == "__main__":
    # 示例 1: nums=[1,3,-1,-3,5,3,6,7], k=3 → [3,3,5,5,6,7]
    assert maxSlidingWindow([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    # 示例 2: nums=[1], k=1 → [1]
    assert maxSlidingWindow([1], 1) == [1]
    print("全部测试通过")
