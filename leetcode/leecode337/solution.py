"""
考点：树、DFS、动态规划、二叉树
题目：House Robber III（打家劫舍III）—— LeetCode 337
题目描述：二叉树排列的房屋不能同时偷相邻节点，求最大金额
思路：树形 DP。DFS 返回 [rob, notRob] 两个状态。
      rob = node.val + left.notRob + right.notRob
      notRob = max(left) + max(right)
时间复杂度：O(n)
空间复杂度：O(h)
"""

from __future__ import annotations


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None) -> None:
        self.val: int = val
        self.left: TreeNode | None = left
        self.right: TreeNode | None = right


def rob(root: TreeNode | None) -> int:
    """
    树形 DP：每个节点返回两个值 [偷当前节点的最大值, 不偷当前节点的最大值]
    返回类型使用 tuple[int, int] 表示 (rob, not_rob)
    """

    def dfs(node: TreeNode | None) -> tuple[int, int]:
        """DFS 后序遍历，返回 (偷node的最大收益, 不偷node的最大收益)"""
        if node is None:
            return (0, 0)

        left_rob, left_not = dfs(node.left)
        right_rob, right_not = dfs(node.right)

        # 偷当前节点：则左右子节点都不能偷
        rob_val = node.val + left_not + right_not
        # 不偷当前节点：左右子节点可偷可不偷，每个取最大值
        not_rob = max(left_rob, left_not) + max(right_rob, right_not)

        return (rob_val, not_rob)

    rob_root, not_rob_root = dfs(root)
    return max(rob_root, not_rob_root)


if __name__ == "__main__":
    # 测试1：    3
    #          /   \
    #         2     3
    #          \     \
    #           3     1
    root1 = TreeNode(3)
    root1.left = TreeNode(2)
    root1.right = TreeNode(3)
    root1.left.right = TreeNode(3)
    root1.right.right = TreeNode(1)
    assert rob(root1) == 7  # 偷 3(root) + 3(grandchild) + 1 = 7

    # 测试2：    3
    #          /   \
    #         4     5
    #        / \     \
    #       1   3     1
    root2 = TreeNode(3)
    root2.left = TreeNode(4)
    root2.right = TreeNode(5)
    root2.left.left = TreeNode(1)
    root2.left.right = TreeNode(3)
    root2.right.right = TreeNode(1)
    assert rob(root2) == 9  # 偷 4 + 5 = 9

    # 测试3：空树
    assert rob(None) == 0

    print("所有断言通过！")
