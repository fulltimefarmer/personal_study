"""
考点：Array, Hash Table, Divide and Conquer, Counting, Sorting
题目：Majority Element（多数元素）
思路：Boyer-Moore 投票算法。count=0 时更新候选，相等则 count++，不等则 count--。
      多数元素出现超过一半，最终 candidate 即为答案。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def majorityElement(nums: list[int]) -> int:
    # Boyer-Moore 投票算法：多数元素出现次数 > n/2
    candidate = nums[0]  # 初始化候选为第一个元素
    count = 0

    for num in nums:
        if count == 0:
            # count 归零时更新候选元素
            candidate = num
        # 当前元素与候选相同时 count+1，否则 count-1
        count += 1 if num == candidate else -1

    return candidate


if __name__ == "__main__":
    # 示例 1: [3,2,3] → 3
    assert majorityElement([3, 2, 3]) == 3
    # 示例 2: [2,2,1,1,1,2,2] → 2
    assert majorityElement([2, 2, 1, 1, 1, 2, 2]) == 2
    print("全部测试通过")
