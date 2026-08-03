"""
考点：栈, 数组, 单调栈
题目：Daily Temperatures（每日温度）
题目描述：给定温度数组 temperatures，返回 answer[i] 表示第 i 天后要等几天才能遇到更高的温度。没有更高的则 answer[i]=0。
思路：单调递减栈。遍历温度，当栈非空且当前温度大于栈顶温度时，弹出栈顶并计算出差值。将当前索引入栈。
时间复杂度：O(n)
空间复杂度：O(n)
"""


def dailyTemperatures(temperatures: list[int]) -> list[int]:
    n = len(temperatures)
    answer = [0] * n  # 结果数组，默认值为 0
    stack: list[int] = []  # 单调递减栈，存储索引（不是温度值）

    for i, t in enumerate(temperatures):
        # 当栈非空且当前温度高于栈顶索引对应的温度时，弹出并计算等待天数
        while stack and t > temperatures[stack[-1]]:
            prev_idx = stack.pop()
            # 等待天数 = 当前索引 - 栈中索引
            answer[prev_idx] = i - prev_idx
        # 将当前索引入栈，维持栈内温度递减
        stack.append(i)

    # 栈中剩余的索引在右边没有更高的温度，answer 保持默认值 0
    return answer


if __name__ == "__main__":
    # 示例：[73,74,75,71,69,72,76,73] → 输出: [1,1,4,2,1,1,0,0]
    assert dailyTemperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    # 示例：[30,40,50,60] → 输出: [1,1,1,0]
    assert dailyTemperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    # 示例：[30,60,90] → 输出: [1,1,0]
    assert dailyTemperatures([30, 60, 90]) == [1, 1, 0]
