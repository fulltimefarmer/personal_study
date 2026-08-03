"""
考点：数组、双指针（快慢指针 / Floyd 判圈算法）
题目：Find the Duplicate Number（寻找重复数）—— LeetCode 287
题目描述：数组中有 n+1 个数，值在 [1,n] 范围，只有一个重复数，找出它。
         要求不修改数组，O(1) 额外空间。
思路：将数组看作链表，nums[i] 是 i 的后继。有重复数必成环。
      快慢指针找环的入口，即 Floyd 判圈算法。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def findDuplicate(nums: list[int]) -> int:
    # 阶段一：快慢指针相遇，检测环的存在
    # 将数组看作链表：节点 i 的 next 指向 nums[i]
    slow: int = nums[0]
    fast: int = nums[0]

    # Python 没有 do-while，用 while True 配合 break 模拟
    while True:
        slow = nums[slow]  # 慢指针走一步：slow = nums[slow]
        fast = nums[nums[fast]]  # 快指针走两步：fast = nums[nums[fast]]
        if slow == fast:
            break

    # 阶段二：找环的入口（即重复数）
    # 将一个指针重置到起点，两个指针同速前进，相遇点即为环的入口
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]

    return slow  # 返回环的入口，即重复的数


if __name__ == "__main__":
    assert findDuplicate([1, 3, 4, 2, 2]) == 2
    assert findDuplicate([3, 1, 3, 4, 2]) == 3
    assert findDuplicate([1, 1]) == 1
    assert findDuplicate([2, 2, 2, 2, 2]) == 2
    print("所有断言通过！")
