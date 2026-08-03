"""
考点：Union Find, Array, Hash Table
题目：Longest Consecutive Sequence（最长连续序列）
题目描述：找出未排序数组中数字连续的最长序列长度，要求 O(n) 时间。
示例 1：[100,4,200,1,3,2]，输出 4（[1,2,3,4]）
示例 2：[0,3,7,2,5,8,4,6,0,1]，输出 9
思路：HashSet，只有当 num-1 不在集合中时才开始查找，保证每个数字最多访问两次。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def longestConsecutive(nums: list[int]) -> int:
    num_set: set[int] = set(nums)  # 转为集合，O(1) 查找
    max_len: int = 0

    for num in num_set:
        # 只有当 num-1 不在集合中时，num 才可能是连续序列的起点
        # 这个条件保证每个序列只从起点开始扩展一次，实现 O(n)
        if num - 1 not in num_set:
            current_num: int = num
            current_len: int = 1

            # 向后查找连续的数字
            while current_num + 1 in num_set:
                current_num += 1
                current_len += 1

            max_len = max(max_len, current_len)

    return max_len


if __name__ == "__main__":
    assert longestConsecutive([100, 4, 200, 1, 3, 2]) == 4
    assert longestConsecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
    assert longestConsecutive([]) == 0
    assert longestConsecutive([1]) == 1
