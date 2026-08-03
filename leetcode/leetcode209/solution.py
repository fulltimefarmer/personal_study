"""
考点：数组、滑动窗口、双指针
题目：Minimum Size Subarray Sum（长度最小的子数组）
题目描述：给定正整数数组 nums 和目标值 target，找出和 >= target 的最短连续子数组长度。
  示例：target = 7, nums = [2,3,1,2,4,3] → 2（子数组 [4,3]）
思路：滑动窗口。维护窗口 [left, right]，窗口和 sum。
  当 sum >= target 时，记录长度并缩小左边界；否则扩大右边界。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def minSubArrayLen(target: int, nums: list[int]) -> int:
    left = 0
    window_sum = 0
    # 初始化为无穷大，方便取最小值
    min_len = float("inf")

    for right in range(len(nums)):
        window_sum += nums[right]  # 扩展右边界，加入当前元素

        # 当窗口和满足条件时，尝试收缩左边界以寻找更短的子数组
        while window_sum >= target:
            min_len = min(min_len, right - left + 1)  # 更新最小长度
            window_sum -= nums[left]  # 窗口左边界右移，移除左边元素
            left += 1

    # 如果 min_len 没有更新，说明无解
    return 0 if min_len == float("inf") else int(min_len)  # float("inf") 是 float 类型，转为 int


if __name__ == "__main__":
    assert minSubArrayLen(7, [2, 3, 1, 2, 4, 3]) == 2
    assert minSubArrayLen(4, [1, 4, 4]) == 1
    assert minSubArrayLen(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0
    assert minSubArrayLen(15, [1, 2, 3, 4, 5]) == 5
