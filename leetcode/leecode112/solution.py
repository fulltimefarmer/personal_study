"""
考点：Tree, DFS, BFS, Binary Tree
题目：Path Sum（路径总和）
题目描述：给定一个二叉树和一个目标和，判断该树中是否存在根节点到叶子节点的路径，这条路径上所有节点值相加等于目标和。
叶子节点是指没有子节点的节点。
示例 1：root = [5,4,8,11,None,13,4,7,2,None,None,None,1], targetSum = 22，输出 true
示例 2：root = [1,2,3], targetSum = 5，输出 false
示例 3：root = [], targetSum = 0，输出 false
思路：DFS 递归，每次减去当前节点值，到达叶子节点时检查剩余值是否为 0。
时间复杂度：O(n)
空间复杂度：O(h)
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def hasPathSum(root: TreeNode | None, targetSum: int) -> bool:
    # 空树不存在任何路径
    if root is None:
        return False
    # 减去当前节点值后的剩余目标和
    remaining: int = targetSum - root.val
    # 叶子节点：左右子节点都为空，此时检查剩余值是否为 0
    if root.left is None and root.right is None:
        return remaining == 0
    # 非叶子节点：递归检查左右子树，任一满足即可（短路求值）
    return hasPathSum(root.left, remaining) or hasPathSum(root.right, remaining)


if __name__ == "__main__":
    # [5,4,8,11,None,13,4,7,2,None,None,None,1], targetSum=22 → True
    root = TreeNode(5)
    root.left = TreeNode(4)
    root.right = TreeNode(8)
    root.left.left = TreeNode(11)
    root.left.left.left = TreeNode(7)
    root.left.left.right = TreeNode(2)
    root.right.left = TreeNode(13)
    root.right.right = TreeNode(4)
    root.right.right.right = TreeNode(1)
    assert hasPathSum(root, 22) is True
    # [1,2,3], targetSum=5 → False
    root2 = TreeNode(1, TreeNode(2), TreeNode(3))
    assert hasPathSum(root2, 5) is False
    assert hasPathSum(None, 0) is False
