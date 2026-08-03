"""
考点：树, DFS, 二叉树
题目：Diameter of Binary Tree（二叉树的直径）
题目描述：给定一棵二叉树，求直径（任意两节点间最长路径的边数）。
思路：DFS 后序遍历。递归计算每个节点的左右子树深度，经过当前节点的路径长为 left+right，全局更新最大值。
时间复杂度：O(n)
空间复杂度：O(h)
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def diameterOfBinaryTree(root: TreeNode | None) -> int:
    # 使用闭包捕获外部变量 diameter，避免传递引用
    diameter = 0

    def depth(node: TreeNode | None) -> int:
        """返回节点 node 的最大深度，同时更新全局直径"""
        nonlocal diameter  # 声明使用外层非全局变量
        if node is None:
            return 0

        # 递归计算左右子树深度（后序遍历）
        left = depth(node.left)
        right = depth(node.right)

        # 经过当前节点的路径长度为 left + right（边数），更新全局最大值
        diameter = max(diameter, left + right)

        # 返回当前节点的深度 = 左右子树深度较大值 + 1（加上当前节点到父节点的边）
        return max(left, right) + 1

    depth(root)
    return diameter


if __name__ == "__main__":
    # 示例：root=[1,2,3,4,5] → 输出: 3（路径 [4,2,1,3] 或 [5,2,1,3]）
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)
    assert diameterOfBinaryTree(root) == 3

    # 单节点树 → 输出: 0
    assert diameterOfBinaryTree(TreeNode(0)) == 0
