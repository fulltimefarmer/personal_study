"""
考点：数学, 二分搜索, 动态规划
题目：Super Egg Drop（鸡蛋掉落）
题目描述：k 个鸡蛋，n 层楼。找到临界楼层 f，鸡蛋在 f 层及以上会碎。求最坏情况下确定 f 所需的最小操作次数。
思路：DP 基于移动次数。dp[m][k] 表示 m 次移动、k 个鸡蛋可确定的最大楼层数。递推：dp[m][k] = dp[m-1][k-1] + dp[m-1][k] + 1（碎了楼下 + 没碎楼上 + 当前层）。m 从 1 增加直到 dp[m][k] >= n。
时间复杂度：O(k * m)
空间复杂度：O(k)
"""


def superEggDrop(k: int, n: int) -> int:
    # dp[i] 表示在当前移动次数下，有 i 个鸡蛋能确定的最大楼层数
    # 用一维数组滚动优化，索引 0 不用
    dp = [0] * (k + 1)
    moves = 0

    # 当 k 个鸡蛋能确定的楼层数还不足 n 时，增加一次移动
    while dp[k] < n:
        moves += 1
        # 倒序遍历鸡蛋数，因为计算新的 dp[i] 需要用到上一轮移动中的 dp[i-1]
        # 倒序保证 dp[i-1] 还是上一轮的值（还未被更新）
        for i in range(k, 0, -1):
            # dp[i] = dp[i-1](上一轮,i-1个蛋) + dp[i](上一轮,i个蛋) + 1
            # 碎: 检查 dp[moves-1][i-1] 层楼以下
            # 不碎: 检查 dp[moves-1][i] 层楼以上
            # +1: 当前测试的这一层
            dp[i] = dp[i] + dp[i - 1] + 1

    return moves


if __name__ == "__main__":
    # 示例：k=1, n=2 → 输出: 2（只有一个鸡蛋，必须从 1 楼开始逐层尝试）
    assert superEggDrop(1, 2) == 2
    # 示例：k=2, n=6 → 输出: 3
    assert superEggDrop(2, 6) == 3
    # 示例：k=3, n=14 → 输出: 4
    assert superEggDrop(3, 14) == 4
