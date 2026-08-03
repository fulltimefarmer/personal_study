"""
考点：数组、双指针
题目：Rotate Array（轮转数组）
题目描述：将数组中的元素向右轮转 k 次。要求原地算法，空间 O(1)。
  示例：nums = [1,2,3,4,5,6,7], k = 3 → [5,6,7,1,2,3,4]
思路：三次反转法。
  1. 反转整个数组
  2. 反转前 k % n 个元素
  3. 反转后 n - k % n 个元素
时间复杂度：O(n)
空间复杂度：O(1)
"""


def rotate(nums: list[int], k: int) -> None:
    n = len(nums)
    k %= n  # k 可能大于 n，取模避免多余操作

    # 辅助函数：反转 nums 中 [left, right) 区间的元素
    def reverse(left: int, right: int) -> None:
        right -= 1  # 转为闭区间 [left, right]
        while left < right:
            nums[left], nums[right] = nums[right], nums[left]  # 交换两端元素
            left += 1
            right -= 1

    # 三步反转：
    # 原始：[1,2,3,4,5,6,7], k=3
    # 第一步反转全部：[7,6,5,4,3,2,1]
    reverse(0, n)
    # 第二步反转前 k 个：[5,6,7,4,3,2,1]
    reverse(0, k)
    # 第三步反转剩余：[5,6,7,1,2,3,4]
    reverse(k, n)


if __name__ == "__main__":
    nums1 = [1, 2, 3, 4, 5, 6, 7]
    rotate(nums1, 3)
    assert nums1 == [5, 6, 7, 1, 2, 3, 4]

    nums2 = [-1, -100, 3, 99]
    rotate(nums2, 2)
    assert nums2 == [3, 99, -1, -100]
