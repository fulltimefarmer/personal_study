"""
考点：数组、哈希表（原地标记）
题目：Find All Numbers Disappeared in an Array（找到所有数组中消失的数字）—— LeetCode 448
题目描述：找出 [1, n] 中未出现在数组 nums 中的数字
思路：原地标记。遍历数组，将 nums[abs(nums[i]) - 1] 标记为负数。
      再遍历一次，正数位置的索引 + 1 即为缺失数字。
时间复杂度：O(n)
空间复杂度：O(1)
"""

def findDisappearedNumbers(nums: list[int]) -> list[int]:
    # 第一遍遍历：用正负号标记数字是否出现过
    for i in range(len(nums)):
        # abs(nums[i]) 获取当前元素对应的值（可能已被标记为负数）
        # -1 是因为数组值的范围是 [1, n]，映射到索引 [0, n-1]
        index = abs(nums[i]) - 1
        # 如果该位置的值为正数，标记为负数（表示 index+1 这个数字出现过）
        if nums[index] > 0:
            nums[index] = -nums[index]

    # 第二遍遍历：收集未被标记的位置（值为正数的索引）
    result: list[int] = []
    for i in range(len(nums)):
        if nums[i] > 0:
            # 索引 i 是正数，说明 i+1 从未出现过
            result.append(i + 1)

    return result


if __name__ == "__main__":
    assert findDisappearedNumbers([4, 3, 2, 7, 8, 2, 3, 1]) == [5, 6]
    assert findDisappearedNumbers([1, 1]) == [2]
    assert findDisappearedNumbers([1, 2, 3]) == []
    assert findDisappearedNumbers([2, 2]) == [1]
    assert findDisappearedNumbers([1]) == []
    print("所有断言通过！")
