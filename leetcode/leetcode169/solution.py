"""
考点：数组、哈希表、分治、计数、排序
题目：Majority Element（多数元素）
题目描述：找出数组中出现次数超过 n/2 的元素。题目保证多数元素存在。
  示例：nums = [3,2,3] → 3
思路：Boyer-Moore 投票算法。利用多数元素数量 > n/2 的特性，通过抵消法找出。
  candidate 记录候选元素，count 记录票数。遇到相同元素 count++，不同 count--。
  count 归零时更换 candidate。最终 candidate 即为多数元素。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def majorityElement(nums: list[int]) -> int:
    # Boyer-Moore 投票算法：众数出现次数必然超过其他所有数字出现次数之和
    candidate = nums[0]  # 先假设第一个元素是众数
    count = 1  # 当前候选者的净票数

    for i in range(1, len(nums)):
        if count == 0:
            # 票数归零说明之前的候选者被「抵消」干净了，换新候选者
            candidate = nums[i]
            count = 1
        elif nums[i] == candidate:
            count += 1  # 遇到相同元素，投票支持
        else:
            count -= 1  # 遇到不同元素，投票反对从而抵消

    return candidate  # 题目保证多数元素存在，candidate 即为答案


if __name__ == "__main__":
    assert majorityElement([3, 2, 3]) == 3
    assert majorityElement([2, 2, 1, 1, 1, 2, 2]) == 2
    assert majorityElement([1]) == 1
