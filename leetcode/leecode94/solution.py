"""
考点: Stack, Tree, DFS, Binary Tree
题目: Binary Tree Inorder Traversal（二叉树的中序遍历）
题目描述: 给定二叉树根节点 root，返回中序遍历结果（左 -> 根 -> 右）。
示例: root = [1,null,2,3] -> [1,3,2]
思路: 迭代法。使用栈模拟递归，沿左链入栈，弹出访问后转向右子树。
时间复杂度: O(n)
空间复杂度: O(h)，h 为树高
"""

from __future__ import annotations


class TreeNode:
    """二叉树节点"""
    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None):
        self.val = val
        self.left = left
        self.right = right


def inorderTraversal(root: TreeNode | None) -> list[int]:
    result: list[int] = []
    stack: list[TreeNode] = []
    current = root  # 当前遍历的节点

    # 迭代中序遍历: 栈模拟递归的过程
    # 循环条件: 当前节点非空 或 栈非空（还有未处理的节点）
    while current or stack:
        # 沿着左链一路到底，将所有左子节点入栈
        while current:
            stack.append(current)
            current = current.left

        # 弹出栈顶节点（此时没有左子树或左子树已处理完）
        # list.pop() 默认弹出最后一个元素（栈顶）
        current = stack.pop()
        result.append(current.val)  # 访问根节点（中序: 在左子树之后）

        # 转向右子树继续处理
        current = current.right

    return result


if __name__ == "__main__":
    # 构造树: [1, null, 2, 3]
    #       1
    #        \
    #         2
    #        /
    #       3
    root1 = TreeNode(1, None, TreeNode(2, TreeNode(3)))
    assert inorderTraversal(root1) == [1, 3, 2]

    # 空树
    assert inorderTraversal(None) == []

    # 单节点树
    assert inorderTraversal(TreeNode(1)) == [1]
