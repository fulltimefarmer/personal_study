"""
考点：数组、计数排序
题目：H-Index（H指数）—— LeetCode 274
题目描述：给定论文引用次数数组，求最大 h，使得至少有 h 篇论文被引用至少 h 次
思路：计数排序。统计每个引用次数的论文数量，从高到低累加，
      当累计论文数 >= 当前引用次数时即为 h 指数。
时间复杂度：O(n)
空间复杂度：O(n)
"""

def hIndex(citations: list[int]) -> int:
    n = len(citations)
    # counts[i] 表示引用次数为 i 的论文数量
    # 大小 n+1：引用次数超过 n 的论文统一放入 counts[n]（h 指数不可能超过 n）
    counts = [0] * (n + 1)

    for c in citations:
        # 引用次数超过 n 的论文，对 h 指数的影响最多为 n
        counts[min(c, n)] += 1

    total = 0  # 累计论文数量（从高引用到低引用累加）
    # 从 n 向下遍历，找到满足条件的最大的 i
    for i in range(n, -1, -1):
        total += counts[i]
        # 当引用次数 >= i 的论文数量 total >= i 时，i 即为 h 指数
        if total >= i:
            return i

    return 0


if __name__ == "__main__":
    assert hIndex([3, 0, 6, 1, 5]) == 3
    assert hIndex([1, 3, 1]) == 1
    assert hIndex([0]) == 0
    assert hIndex([100]) == 1
    assert hIndex([11, 15]) == 2
    print("所有断言通过！")
