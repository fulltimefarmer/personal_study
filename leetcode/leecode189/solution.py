"""
考点：数组、数学、双指针
题目：Rotate Array（轮转数组）
思路：三次反转法——反转整个数组，反转前 k 个，反转后 n-k 个。O(1) 空间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def rotate(nums: list[int], k: int) -> None:
    """
    原地将数组向右轮转 k 步（修改原数组，不返回值）。
    """
    n = len(nums)
    k %= n  # k 可能大于 n，取模处理

    def reverse(start: int, end: int) -> None:
        """反转 nums[start:end+1] 区间内的元素"""
        while start < end:
            # Python 交换两个变量（底层是元组解包，不需临时变量）
            nums[start], nums[end] = nums[end], nums[start]
            start += 1
            end -= 1

    # 第一步：反转整个数组
    reverse(0, n - 1)
    # 第二步：反转前 k 个元素
    reverse(0, k - 1)
    # 第三步：反转后 n-k 个元素
    reverse(k, n - 1)


if __name__ == "__main__":
    # 示例: [1,2,3,4,5,6,7], k=3 → [5,6,7,1,2,3,4]
    nums = [1, 2, 3, 4, 5, 6, 7]
    rotate(nums, 3)
    assert nums == [5, 6, 7, 1, 2, 3, 4]
    # 示例: [-1,-100,3,99], k=2 → [3,99,-1,-100]
    nums2 = [-1, -100, 3, 99]
    rotate(nums2, 2)
    assert nums2 == [3, 99, -1, -100]
    print("全部测试通过")
