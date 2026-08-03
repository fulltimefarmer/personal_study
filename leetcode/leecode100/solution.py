"""
考点: Tree, DFS, BFS, Binary Tree
题目: Same Tree（相同的树）
题目描述: 给定两棵二叉树的根节点 p 和 q，判断两棵树是否完全相同（结构和值）。
示例: p = [1,2,3], q = [1,2,3] -> true
示例: p = [1,2], q = [1,null,2] -> false
思路: DFS 递归。同时遍历两棵树，比较对应节点的值。
      都为空返回 true，只有一个为空或值不等返回 false，递归比较左右子树。
时间复杂度: O(min(n1, n2))
空间复杂度: O(h)
"""

from __future__ import annotations


class TreeNode:
    """二叉树节点"""
    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None):
        self.val = val
        self.left = left
        self.right = right


def isSameTree(p: TreeNode | None, q: TreeNode | None) -> bool:
    # 情况一: 两个节点都为空 -> 相同
    if p is None and q is None:
        return True
    # 情况二: 一个为空另一个非空 -> 不同
    if p is None or q is None:
        return False
    # 情况三: 值不相等 -> 不同
    if p.val != q.val:
        return False
    # 递归比较左右子树: 必须同时满足左子树相同且右子树相同
    return isSameTree(p.left, q.left) and isSameTree(p.right, q.right)


if __name__ == "__main__":
    # 树1:     1       树2:     1
    #         / \             / \
    #        2   3           2   3
    t1 = TreeNode(1, TreeNode(2), TreeNode(3))
    t2 = TreeNode(1, TreeNode(2), TreeNode(3))
    assert isSameTree(t1, t2) is True

    # 树3:     1       树4:     1
    #         /               /
    #        2               2
    t3 = TreeNode(1, TreeNode(2))
    t4 = TreeNode(1, None, TreeNode(2))
    assert isSameTree(t3, t4) is False

    # 树5:     1       树6:     1
    #         / \             / \
    #        1   2           2   1
    t5 = TreeNode(1, TreeNode(1), TreeNode(2))
    t6 = TreeNode(1, TreeNode(2), TreeNode(1))
    assert isSameTree(t5, t6) is False

    # 两棵空树
    assert isSameTree(None, None) is True
