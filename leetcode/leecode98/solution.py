"""
考点: Tree, DFS, BST, Binary Tree
题目: Validate Binary Search Tree（验证二叉搜索树）
题目描述: 给定二叉树根节点，判断是否是有效的 BST。
      左子树所有节点小于根，右子树所有节点大于根，且左右子树也是 BST。
示例: root = [2,1,3] -> true
示例: root = [5,1,4,null,null,3,6] -> false
思路: 递归带上下界。每个节点的值必须在 (lower, upper) 范围内。
      左子树更新上界为 root.val，右子树更新下界为 root.val。
时间复杂度: O(n)
空间复杂度: O(h)，h 为树高
"""

from __future__ import annotations
import math


class TreeNode:
    """二叉树节点"""
    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None):
        self.val = val
        self.left = left
        self.right = right


def isValidBST(root: TreeNode | None) -> bool:
    def validate(node: TreeNode | None, lower: float, upper: float) -> bool:
        # 空树是有效的 BST
        if node is None:
            return True
        # 当前节点值必须在开区间 (lower, upper) 内
        # 使用 <= 和 >= 因为 BST 严格定义不允许重复值
        if node.val <= lower or node.val >= upper:
            return False
        # 递归验证左右子树:
        # 左子树: 上界变为 node.val（所有左子节点 < node.val）
        # 右子树: 下界变为 node.val（所有右子节点 > node.val）
        return validate(node.left, lower, node.val) and \
               validate(node.right, node.val, upper)

    # math.inf: Python 3.5+ 的正无穷和负无穷
    # 任意整数都在 (-inf, inf) 范围内
    return validate(root, -math.inf, math.inf)


if __name__ == "__main__":
    # BST:     2
    #         / \
    #        1   3
    root1 = TreeNode(2, TreeNode(1), TreeNode(3))
    assert isValidBST(root1) is True

    # 非 BST:  5
    #         / \
    #        1   4
    #           / \
    #          3   6
    root2 = TreeNode(5, TreeNode(1), TreeNode(4, TreeNode(3), TreeNode(6)))
    assert isValidBST(root2) is False

    # 边界: 空树
    assert isValidBST(None) is True

    # 边界: 单节点
    assert isValidBST(TreeNode(1)) is True
