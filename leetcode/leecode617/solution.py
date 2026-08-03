"""
考点：树, DFS, BFS, 二叉树
题目：Merge Two Binary Trees（合并二叉树）
题目描述：合并两棵二叉树，重叠节点值相加，不重叠的节点保留不为空的。返回合并后的二叉树。
思路：DFS 递归。若任一节点为 None 则返回另一个节点。否则值相加，递归合并左右子树。
时间复杂度：O(min(n1, n2))
空间复杂度：O(min(h1, h2))
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def mergeTrees(root1: TreeNode | None, root2: TreeNode | None) -> TreeNode | None:
    # 如果 root1 为空，直接返回 root2（以及它的子树）
    if root1 is None:
        return root2
    # 如果 root2 为空，直接返回 root1（以及它的子树）
    if root2 is None:
        return root1

    # 两个节点都不为空：值相加，递归合并左右子树
    # 这里直接复用 root1 作为结果树，修改其值
    root1.val += root2.val
    root1.left = mergeTrees(root1.left, root2.left)
    root1.right = mergeTrees(root1.right, root2.right)

    return root1


if __name__ == "__main__":
    # 示例：root1=[1,3,2,5], root2=[2,1,3,null,4,null,7] → 输出: [3,4,5,5,4,null,7]
    root1 = TreeNode(1, TreeNode(3, TreeNode(5)), TreeNode(2))
    root2 = TreeNode(2, TreeNode(1, None, TreeNode(4)), TreeNode(3, None, TreeNode(7)))
    merged = mergeTrees(root1, root2)
    assert merged.val == 3
    assert merged.left.val == 4
    assert merged.right.val == 5
    assert merged.left.left.val == 5
    assert merged.left.right.val == 4
    assert merged.right.right.val == 7
