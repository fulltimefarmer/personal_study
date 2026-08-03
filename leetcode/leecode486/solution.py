"""
考点：递归, 数组, 数学, 动态规划, 博弈论
题目：Predict the Winner（预测赢家）
题目描述：给定 nums，玩家 1 和玩家 2 轮流从数组两端取数，分数加到各自总分。双方都采取最优策略，判断玩家 1 是否能赢（平局也算赢）。
思路：博弈 DP。dp[i][j] 表示 nums[i..j] 中当前先手的最大净胜分。dp[i][j] = max(nums[i]-dp[i+1][j], nums[j]-dp[i][j-1])。最终 dp[0][n-1]>=0 则玩家 1 赢。
时间复杂度：O(n²)
空间复杂度：O(n²)
"""


def predictTheWinner(nums: list[int]) -> bool:
    n = len(nums)
    # dp[i][j] 表示子数组 nums[i..j] 中当前先手玩家的最大净胜分
    # 先手得分 - 后手得分
    dp = [[0] * n for _ in range(n)]

    # 初始化：单个元素时，先手只能取该元素，净胜分就是 nums[i]
    for i in range(n):
        dp[i][i] = nums[i]

    # 按区间长度从小到大递推
    # len 表示子数组长度，从 2 到 n
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            # 两种选择：取左边 nums[i] 或取右边 nums[j]
            # 取左边后，剩余子数组 nums[i+1..j] 中对方是先手，净胜分为 dp[i+1][j]
            # 所以当前净胜分 = nums[i] - dp[i+1][j]
            # 取右边同理
            dp[i][j] = max(nums[i] - dp[i + 1][j], nums[j] - dp[i][j - 1])

    # dp[0][n-1] >= 0 说明玩家 1 净胜分非负（至少不输，平局也算赢）
    return dp[0][n - 1] >= 0


if __name__ == "__main__":
    # 示例：[1,5,2] → 输出: false（玩家 1 无论先取 1 还是 2，玩家 2 都能拿到 5）
    assert predictTheWinner([1, 5, 2]) is False
    # 示例：[1,5,233,7] → 输出: true
    assert predictTheWinner([1, 5, 233, 7]) is True
