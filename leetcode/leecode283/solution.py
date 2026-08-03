"""
考点：数组、双指针
题目：Move Zeroes（移动零）—— LeetCode 283
题目描述：将所有 0 移动到数组末尾，同时保持非零元素的相对顺序，原地操作
思路：双指针。慢指针指向下一个非零元素应放位置，快指针遍历数组，
      遇到非零元素就交换到慢指针位置，慢指针后移。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def moveZeroes(nums: list[int]) -> None:
    # 慢指针 left：指向下一个非零元素应该放置的位置
    left = 0

    # 快指针 right：遍历数组中每个元素
    for right in range(len(nums)):
        if nums[right] != 0:
            # Python 的行内交换（多变量同时赋值），本质上是元组打包/解包
            # 等价于: temp = nums[left]; nums[left] = nums[right]; nums[right] = temp
            nums[left], nums[right] = nums[right], nums[left]
            left += 1  # 慢指针前进，因为当前位置已存放非零元素


if __name__ == "__main__":
    # 基本测试
    arr1 = [0, 1, 0, 3, 12]
    moveZeroes(arr1)
    assert arr1 == [1, 3, 12, 0, 0]

    # 全零
    arr2 = [0, 0, 0]
    moveZeroes(arr2)
    assert arr2 == [0, 0, 0]

    # 无零
    arr3 = [1, 2, 3]
    moveZeroes(arr3)
    assert arr3 == [1, 2, 3]

    # 单元素
    arr4 = [0]
    moveZeroes(arr4)
    assert arr4 == [0]

    print("所有断言通过！")
