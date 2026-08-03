"""
考点：数组、二分查找、前缀和、滑动窗口
题目：Minimum Size Subarray Sum（长度最小的子数组）
思路：滑动窗口。右指针扩展累加 sum，当 sum>=target 时收缩左指针找最短长度。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def minSubArrayLen(target: int, nums: list[int]) -> int:
    left = 0
    total = 0
    # Python 3.12 中 float("inf") 可用于表示正无穷
    min_len: int | float = float("inf")

    for right in range(len(nums)):
        total += nums[right]  # 扩展窗口右边界

        # 当窗口内的和满足条件时，尝试收缩左边界
        while total >= target:
            # 更新最短长度
            min_len = min(min_len, right - left + 1)
            total -= nums[left]  # 移除左边界元素
            left += 1

    return 0 if min_len == float("inf") else int(min_len)


if __name__ == "__main__":
    # 示例 1: target=7, nums=[2,3,1,2,4,3] → 2 (子数组 [4,3])
    assert minSubArrayLen(7, [2, 3, 1, 2, 4, 3]) == 2
    # 示例 2: target=4, nums=[1,4,4] → 1
    assert minSubArrayLen(4, [1, 4, 4]) == 1
    # 示例 3: target=11, nums=[1,1,1,1,1] → 0 (无解)
    assert minSubArrayLen(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0
    print("全部测试通过")
