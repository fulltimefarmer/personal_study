"""
考点：Array, Binary Search
题目：Find Peak Element（寻找峰值）
题目描述：找任意一个峰值（大于左右相邻值），nums[-1]=nums[n]=-∞，O(log n)。
示例 1：[1,2,3,1]，输出 2（峰值 3 的索引）
示例 2：[1,2,1,3,5,6,4]，输出 1 或 5
思路：二分查找，比较 nums[mid] 和 nums[mid+1]。
nums[mid] > nums[mid+1] → 下降趋势，左侧必有峰值 → right = mid
nums[mid] < nums[mid+1] → 上升趋势，右侧必有峰值 → left = mid + 1
时间复杂度：O(log n)
空间复杂度：O(1)
"""


def findPeakElement(nums: list[int]) -> int:
    left: int = 0
    right: int = len(nums) - 1

    while left < right:
        mid: int = (left + right) // 2
        # 比较 mid 和 mid+1 的大小关系判断"趋势"
        # nums[mid] > nums[mid+1]：说明在下降，左侧（含 mid）一定有峰值
        # nums[mid] < nums[mid+1]：说明在上升，右侧一定有峰值
        if nums[mid] > nums[mid + 1]:
            right = mid       # mid 本身可能是峰值
        else:
            left = mid + 1    # mid 一定不是峰值

    return left


if __name__ == "__main__":
    assert findPeakElement([1, 2, 3, 1]) in [2]       # 峰值索引 2
    assert findPeakElement([1, 2, 1, 3, 5, 6, 4]) in [1, 5]
    assert findPeakElement([1]) == 0
    assert findPeakElement([1, 2]) == 1               # nums[-1]=nums[2]=-∞, 2是峰值
    assert findPeakElement([2, 1]) == 0               # nums[-1]=-∞, 2是峰值
