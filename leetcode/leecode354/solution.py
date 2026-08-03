"""
考点：数组、二分查找、动态规划、排序
题目：Russian Doll Envelopes（俄罗斯套娃信封问题）—— LeetCode 354
题目描述：二维信封套娃，要求宽高都更大才能嵌套，求最大信封数
思路：按宽度升序、高度降序排序，对高度求 LIS（贪心+二分）。
      降序确保相同宽度的信封不会被同时选中。
时间复杂度：O(n log n)
空间复杂度：O(n)
"""

import bisect


def maxEnvelopes(envelopes: list[list[int]]) -> int:
    # 排序策略：宽度升序，宽度相同时高度降序
    # 高度降序确保相同宽度的信封不能相互嵌套（因为高度大的排前面会被跳过）
    # Python 的 sort 中 key=lambda x: (x[0], -x[1]) 实现宽度升序、高度降序
    envelopes.sort(key=lambda x: (x[0], -x[1]))

    # 对高度数组求 LIS（最长递增子序列）
    tails: list[int] = []

    for _, h in envelopes:
        pos = bisect.bisect_left(tails, h)
        if pos == len(tails):
            tails.append(h)
        else:
            tails[pos] = h

    return len(tails)


if __name__ == "__main__":
    assert maxEnvelopes([[5, 4], [6, 4], [6, 7], [2, 3]]) == 3  # [2,3] → [5,4] → [6,7]
    assert maxEnvelopes([[1, 1], [1, 1], [1, 1]]) == 1  # 相同宽高不能嵌套
    assert maxEnvelopes([[4, 5], [4, 6], [6, 7], [2, 3], [1, 1]]) == 4
    assert maxEnvelopes([[1, 3], [3, 5], [6, 7], [6, 8], [7, 9]]) == 4  # [1,3]→[3,5]→[6,7]→[7,9] 或 [1,3]→[3,5]→[6,8]→[7,9]
    print("所有断言通过！")
