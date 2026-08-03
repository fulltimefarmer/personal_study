"""
考点: Tree, DFS, BFS, Binary Tree
题目: Symmetric Tree（对称二叉树）
题目描述: 给定二叉树根节点，检查是否轴对称。
示例: root = [1,2,2,3,4,4,3] -> true
示例: root = [1,2,2,null,3,null,3] -> false
思路: DFS 递归。将问题转化为比较左右子树是否互为镜像。
      镜像条件: 值相等，且 left.left 与 right.right 镜像，left.right 与 right.left 镜像。
时间复杂度: O(n)
空间复杂度: O(h)
"""

from __future__ import annotations


class TreeNode:
    """二叉树节点"""
    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None):
        self.val = val
        self.left = left
        self.right = right


def isSymmetric(root: TreeNode | None) -> bool:
    # 空树是对称的
    if root is None:
        return True

    # 将问题转化为: 左右子树是否互为镜像
    return _isMirror(root.left, root.right)


def _isMirror(left: TreeNode | None, right: TreeNode | None) -> bool:
    """
    判断两个子树是否互为镜像。
    镜像条件:
    1. 两个节点都为空 -> 镜像
    2. 一个为空另一个非空 -> 非镜像
    3. 值不相等 -> 非镜像
    4. 递归: left的左子 == right的右子 且 left的右子 == right的左子
    """
    # 两个节点都为空
    if left is None and right is None:
        return True
    # 只有一个为空
    if left is None or right is None:
        return False
    # 值不相等
    if left.val != right.val:
        return False
    # 递归比较: 外层(left.left vs right.right) 和内层 (left.right vs right.left)
    return _isMirror(left.left, right.right) and _isMirror(left.right, right.left)


if __name__ == "__main__":
    # 对称树:       1
    #            /     \
    #           2       2
    #          / \     / \
    #         3   4   4   3
    root1 = TreeNode(1,
                     TreeNode(2, TreeNode(3), TreeNode(4)),
                     TreeNode(2, TreeNode(4), TreeNode(3)))
    assert isSymmetric(root1) is True

    # 非对称树:     1
    #            /     \
    #           2       2
    #            \       \
    #             3       3
    root2 = TreeNode(1,
                     TreeNode(2, None, TreeNode(3)),
                     TreeNode(2, None, TreeNode(3)))
    assert isSymmetric(root2) is False

    # 单节点树
    assert isSymmetric(TreeNode(1)) is True

    # 空树
    assert isSymmetric(None) is True
