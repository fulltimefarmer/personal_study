"""
考点：数组、前缀和（前缀积）
题目：Product of Array Except Self（除自身以外数组的乘积）
思路：第一遍从左到右累积左乘积存入 answer；第二遍从右到左累积右乘积乘入 answer。
时间复杂度：O(n)
空间复杂度：O(1)（不计结果数组）
"""


def productExceptSelf(nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [0] * n

    # 第一遍：从左到右，answer[i] = nums[0] * ... * nums[i-1]
    answer[0] = 1
    for i in range(1, n):
        answer[i] = answer[i - 1] * nums[i - 1]

    # 第二遍：从右到左，每个位置乘上右侧元素的乘积
    right_product = 1  # 右侧元素乘积
    for i in range(n - 1, -1, -1):
        answer[i] *= right_product
        right_product *= nums[i]

    return answer


if __name__ == "__main__":
    # 示例 1: [1,2,3,4] → [24,12,8,6]
    assert productExceptSelf([1, 2, 3, 4]) == [24, 12, 8, 6]
    # 示例 2: [-1,1,0,-3,3] → [0,0,9,0,0]
    assert productExceptSelf([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    print("全部测试通过")
