"""
考点：递归, 记忆化搜索, 数学, 动态规划
题目：Fibonacci Number（斐波那契数）
题目描述：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)（n>1）。给定 n，计算 F(n)。
思路：动态规划迭代法。用两个变量 prev2 和 prev1 分别保存 F(n-2) 和 F(n-1)，迭代计算即可，避免递归的重复计算和额外的数组空间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


def fib(n: int) -> int:
    if n <= 1:
        return n

    # prev2 保存 F(i-2)，prev1 保存 F(i-1)
    prev2 = 0  # F(0)
    prev1 = 1  # F(1)

    # 从 F(2) 开始迭代到 F(n)
    for _ in range(2, n + 1):
        # curr = F(i-1) + F(i-2)
        curr = prev1 + prev2
        # 滚动更新：prev2 前进到 prev1，prev1 前进到 curr
        prev2 = prev1
        prev1 = curr

    return prev1


if __name__ == "__main__":
    # 示例：n=2 → 输出: 1
    assert fib(2) == 1
    # 示例：n=4 → 输出: 3
    assert fib(4) == 3
    # 示例：n=0 → 输出: 0
    assert fib(0) == 0
