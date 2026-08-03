"""
考点：数组, 数学, 动态规划, 博弈论
题目：Stone Game（石子游戏）
题目描述：偶数堆石子排成一行，Alice 和 Bob 轮流从两端取整堆，取完比大小。Alice 先手，双方最优策略。判断 Alice 是否能赢。
思路：数学结论。偶数堆 + 石子总数为奇数 => Alice 可以控制拿全部偶数索引或奇数索引的堆，二者和必然不相等，Alice 只要选总和大的那一组必赢。因此直接返回 True。
时间复杂度：O(1)
空间复杂度：O(1)
"""


def stoneGame(piles: list[int]) -> bool:
    # 题目条件保证了 piles 长度为偶数，且 Alice 先手
    # Alice 可以确保自己拿到所有偶数索引堆或所有奇数索引堆中总和更大的那组
    # 因此 Alice 必胜，直接返回 True
    # 从 DP 角度看：dp[i][j] = max(piles[i]-dp[i+1][j], piles[j]-dp[i][j-1])，dp[0][n-1] 始终 > 0
    return True


if __name__ == "__main__":
    # 示例：[5,3,4,5] → 输出: true
    assert stoneGame([5, 3, 4, 5]) is True
    # 示例：[3,7,2,3] → 输出: true
    assert stoneGame([3, 7, 2, 3]) is True
