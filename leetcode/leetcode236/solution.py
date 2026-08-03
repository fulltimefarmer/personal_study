"""
考点：树、深度优先搜索、二叉树
题目：Lowest Common Ancestor of a Binary Tree（二叉树的最近公共祖先）
题目描述：给定二叉树 root 和两个节点 p、q，找到它们的最近公共祖先（LCA）。
  示例：root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1 → 3
思路：递归后序遍历。在左右子树中分别寻找 p 和 q。
  - 如果当前节点是 p 或 q 则返回当前节点
  - 如果左右子树各找到一个节点，当前节点就是 LCA
  - 如果只有一侧找到，则返回那一侧的结果（p/q 在那一侧）
时间复杂度：O(n)
空间复杂度：O(h)（递归栈深度）
"""


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def lowestCommonAncestor(root: TreeNode | None, p: TreeNode, q: TreeNode) -> TreeNode | None:
    # 递归终止条件：到达空节点 或 找到 p/q 之一
    if root is None or root == p or root == q:
        return root

    # 分别在左右子树中搜索 p 和 q
    left = lowestCommonAncestor(root.left, p, q)
    right = lowestCommonAncestor(root.right, p, q)

    # 如果左右子树各找到一个节点，说明 p 和 q 分别在当前节点的左右两侧
    # 则当前节点就是 LCA
    if left and right:
        return root

    # 只有一侧找到，返回那一侧的结果（该侧包含了 p 或 q，或者就是 LCA）
    # 使用 Python 的 or 运算符：返回第一个 truthy 值
    return left or right


if __name__ == "__main__":
    # 构建树：
    #       3
    #      / \
    #     5   1
    #    / \ / \
    #   6  2 0  8
    #     / \
    #    7   4
    root = TreeNode(3)
    n5 = TreeNode(5)
    n1 = TreeNode(1)
    n6 = TreeNode(6)
    n2 = TreeNode(2)
    n0 = TreeNode(0)
    n8 = TreeNode(8)
    n7 = TreeNode(7)
    n4 = TreeNode(4)
    root.left = n5
    root.right = n1
    n5.left = n6
    n5.right = n2
    n1.left = n0
    n1.right = n8
    n2.left = n7
    n2.right = n4

    assert lowestCommonAncestor(root, n5, n1) == root  # 3
    assert lowestCommonAncestor(root, n5, n4) == n5  # 5
    assert lowestCommonAncestor(root, n7, n4) == n2  # 2
