"""
考点：Tree, DFS, DP, Binary Tree
题目：Binary Tree Maximum Path Sum（二叉树中的最大路径和）
题目描述：求二叉树中最大路径和。路径起点和终点任意，至少包含一个节点，不一定经过根。
示例 1：[1,2,3]，输出 6（2→1→3）
示例 2：[-10,9,20,None,None,15,7]，输出 42（15→20→7）
思路：DFS 后序遍历，计算每个节点的最大贡献（单边最大路径），更新全局最大值。
当前节点为根的路径和 = val + max(0, 左贡献) + max(0, 右贡献)。
向上贡献 = val + max(0, max(左贡献, 右贡献))（只能选一边）。
时间复杂度：O(n)
空间复杂度：O(h)
"""
import math


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def maxPathSum(root: TreeNode | None) -> int:
    # 使用 float("-inf") 作为初始最大值，处理全负数节点的情况
    max_sum: float = float("-inf")

    def max_gain(node: TreeNode | None) -> int:
        nonlocal max_sum
        if node is None:
            return 0
        # 左子树最大贡献，负数则不选（取 0）
        left_gain: int = max(max_gain(node.left), 0)
        # 右子树最大贡献，负数则不选（取 0）
        right_gain: int = max(max_gain(node.right), 0)
        # 以当前节点为根的完整路径和
        current_sum: int = node.val + left_gain + right_gain
        # 更新全局最大值
        max_sum = max(max_sum, current_sum)
        # 向上返回：当前节点值 + 左右中较大的贡献（只能选一边构成路径）
        return node.val + max(left_gain, right_gain)

    max_gain(root)
    return int(max_sum)


if __name__ == "__main__":
    # 示例 1：[1,2,3] → 6
    root1 = TreeNode(1, TreeNode(2), TreeNode(3))
    assert maxPathSum(root1) == 6
    # 示例 2：[-10,9,20,None,None,15,7] → 42
    root2 = TreeNode(-10)
    root2.left = TreeNode(9)
    root2.right = TreeNode(20, TreeNode(15), TreeNode(7))
    assert maxPathSum(root2) == 42
    # 负数节点
    assert maxPathSum(TreeNode(-3)) == -3
