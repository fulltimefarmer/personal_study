from typing import List, Optional


class TreeNode:
    """二叉树节点。"""

    def __init__(
        self,
        val: int = 0,
        left: Optional["TreeNode"] = None,
        right: Optional["TreeNode"] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right


def zigzagLevelOrder(root: Optional[TreeNode]) -> List[List[int]]:
    """返回二叉树的锯齿形层序遍历。"""
    pass
