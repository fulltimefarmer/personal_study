"""
考点：Tree, DFS, BFS, Binary Tree
题目：Maximum Depth of Binary Tree（二叉树的最大深度）
题目描述：给定二叉树，返回从根到最远叶子节点的最长路径上的节点数。
示例：root = [3,9,20,None,None,15,7] → 3
思路：DFS 递归。最大深度 = 1 + max(左子树深度, 右子树深度)。
时间复杂度：O(n)
空间复杂度：O(h)
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def maxDepth(root: TreeNode | None) -> int:
    # 空树深度为 0，叶子节点到达这里后返回 0
    if not root:
        return 0
    # 当前层的深度 = 1（当前节点） + 左右子树中较大的深度
    return 1 + max(maxDepth(root.left), maxDepth(root.right))


if __name__ == "__main__":
    root = TreeNode(3)
    root.left = TreeNode(9)
    root.right = TreeNode(20)
    root.right.left = TreeNode(15)
    root.right.right = TreeNode(7)
    assert maxDepth(root) == 3
    assert maxDepth(None) == 0
    assert maxDepth(TreeNode(1)) == 1
