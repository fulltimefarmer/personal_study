"""
考点: Tree, BST, Math, Dynamic Programming, Binary Tree
题目: Unique Binary Search Trees（不同的二叉搜索树）
题目描述: 给定 n 个节点，节点值为 1..n，求能构成的不同二叉搜索树种数。
示例: n = 3 -> 5
思路: 动态规划（卡特兰数）。dp[i] = Sum dp[j-1] * dp[i-j]，j 作为根节点。
      dp[0] = 1 表示空树。
时间复杂度: O(n^2)
空间复杂度: O(n)
"""


def numTrees(n: int) -> int:
    # n=0 或 n=1 返回 1，避免数组越界
    if n <= 1:
        return 1

    # dp[i]: i 个有序节点能构成的不同 BST 数量
    # dp[0] = 1（空树视为 1 种）
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1  # 1 个节点只有 1 种 BST

    # 计算节点数为 2 到 n 的结果
    for i in range(2, n + 1):
        # 枚举根节点 j（1 到 i）
        # 以 j 为根时，左子树有 j-1 个节点（节点值 1..j-1），右子树有 i-j 个节点（j+1..i）
        for j in range(1, i + 1):
            # 左子树的 BST 数 * 右子树的 BST 数 = 以 j 为根的 BST 数
            # 累加所有可能的根节点
            dp[i] += dp[j - 1] * dp[i - j]

    return dp[n]


if __name__ == "__main__":
    assert numTrees(0) == 1
    assert numTrees(1) == 1
    assert numTrees(2) == 2   # [1->2, 2->1]
    assert numTrees(3) == 5   # 卡特兰数 C_3
    assert numTrees(4) == 14  # 卡特兰数 C_4
