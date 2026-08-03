"""
考点：树、DFS、二叉树
题目：Lowest Common Ancestor of a Binary Tree（二叉树的最近公共祖先）
思路：后序遍历，在左右子树找 p/q。若左右都有，则当前是 LCA；否则返回有值的那一侧。
时间复杂度：O(n)
空间复杂度：O(h)，h 为树高
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def lowestCommonAncestor(
    root: TreeNode | None,
    p: TreeNode | None,
    q: TreeNode | None,
) -> TreeNode | None:
    # 递归终止条件：空节点 或 找到 p/q 之一
    if root is None or root is p or root is q:
        return root

    # 后序遍历：先递归左右子树
    left = lowestCommonAncestor(root.left, p, q)
    right = lowestCommonAncestor(root.right, p, q)

    # 如果左右子树都非空，说明 p 和 q 分别在左右子树中，当前根即为 LCA
    if left is not None and right is not None:
        return root

    # 否则返回非空的那一侧（p 和 q 在同一个子树中）
    return left if left is not None else right


if __name__ == "__main__":
    # 构建树: [3,5,1,6,2,0,8,None,None,7,4]
    root = TreeNode(3)
    root.left = TreeNode(5)
    root.right = TreeNode(1)
    root.left.left = TreeNode(6)
    root.left.right = TreeNode(2)
    root.left.right.left = TreeNode(7)
    root.left.right.right = TreeNode(4)
    root.right.left = TreeNode(0)
    root.right.right = TreeNode(8)

    p = root.left           # 5
    q = root.right          # 1
    # p=5, q=1 → LCA=3
    assert lowestCommonAncestor(root, p, q) is root

    p2 = root.left          # 5
    q2 = root.left.right.right  # 4
    # p=5, q=4 → LCA=5
    assert lowestCommonAncestor(root, p2, q2) is p2
    print("全部测试通过")
