"""
考点：Array, Two Pointers, Binary Search
题目：Two Sum II - Input Array Is Sorted（两数之和 II）
思路：双指针，和小则左指针右移，和大则右指针左移。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def twoSum(numbers: list[int], target: int) -> list[int]:
    # 双指针：left 从最左开始，right 从最右开始
    left = 0
    right = len(numbers) - 1

    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            # 题目要求返回 1-based 下标
            return [left + 1, right + 1]
        elif s < target:
            # 和太小，左指针右移增大和
            left += 1
        else:
            # 和太大，右指针左移减小和
            right -= 1

    return [-1, -1]  # 题目保证有解，这行不会执行到


if __name__ == "__main__":
    # 示例 1: [2,7,11,15], target=9 → [1,2]
    assert twoSum([2, 7, 11, 15], 9) == [1, 2]
    # 示例 2: [2,3,4], target=6 → [1,3]
    assert twoSum([2, 3, 4], 6) == [1, 3]
    # 示例 3: [-1,0], target=-1 → [1,2]
    assert twoSum([-1, 0], -1) == [1, 2]
    print("全部测试通过")
