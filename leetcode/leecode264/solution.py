"""
考点：数学、动态规划（三指针）
题目：Ugly Number II（丑数II）—— LeetCode 264
题目描述：找出第 n 个只包含质因数 2、3、5 的丑数
思路：动态规划 + 三指针。dp[i] 是第 i 个丑数，p2/p3/p5 分别指向
      下一个将要乘以 2/3/5 的丑数位置，每次取最小值并移动对应指针。
时间复杂度：O(n)
空间复杂度：O(n)
"""

def nthUglyNumber(n: int) -> int:
    # dp[i] 表示第 i 个丑数，使用 1-index 更方便理解
    dp: list[int] = [0] * (n + 1)
    dp[1] = 1  # 第 1 个丑数是 1

    # 三指针：p2/p3/p5 分别指向下一个可与 2/3/5 相乘产生候选丑数的位置
    p2 = p3 = p5 = 1

    for i in range(2, n + 1):
        # 计算三个候选值
        num2 = dp[p2] * 2
        num3 = dp[p3] * 3
        num5 = dp[p5] * 5

        # 取最小值作为第 i 个丑数
        dp[i] = min(num2, num3, num5)

        # 使用 if 而非 elif：确保在出现重复值（如 2*3 == 3*2）时所有对应指针都前进
        if dp[i] == num2:
            p2 += 1
        if dp[i] == num3:
            p3 += 1
        if dp[i] == num5:
            p5 += 1

    return dp[n]


if __name__ == "__main__":
    assert nthUglyNumber(1) == 1
    assert nthUglyNumber(10) == 12  # 前10个丑数: 1,2,3,4,5,6,8,9,10,12
    assert nthUglyNumber(2) == 2
    assert nthUglyNumber(3) == 3
    assert nthUglyNumber(4) == 4
    assert nthUglyNumber(5) == 5
    print("所有断言通过！")
