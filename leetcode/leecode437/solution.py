"""
考点：树、DFS、二叉树、前缀和
题目：Path Sum III（路径总和III）—— LeetCode 437
题目描述：求二叉树中路径和等于 targetSum 的路径数（路径必须向下）
思路：前缀和 + 哈希表。DFS 维护根到当前节点的路径和 cur_sum，
      在哈希表中查找 cur_sum - targetSum 的出现次数。
      回溯时从哈希表移除当前路径和。
时间复杂度：O(n)
空间复杂度：O(h)
"""

from __future__ import annotations
from collections import defaultdict


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None) -> None:
        self.val: int = val
        self.left: TreeNode | None = left
        self.right: TreeNode | None = right


def pathSum(root: TreeNode | None, targetSum: int) -> int:
    # prefix_count 记录从根到当前节点路径上所有前缀和的出现次数
    # key 是前缀和，value 是该前缀和出现的次数
    # collections.defaultdict(int) 在访问不存在的 key 时自动返回 0
    prefix_count: dict[int, int] = defaultdict(int)
    prefix_count[0] = 1  # 前缀和为 0 出现一次（空路径），处理从根开始的路径

    def dfs(node: TreeNode | None, cur_sum: int) -> int:
        """DFS 后序遍历统计路径和等于 targetSum 的路径数"""
        if node is None:
            return 0

        # 更新当前路径和
        cur_sum += node.val
        # 查找 cur_sum - targetSum 的出现次数：代表有多少条"从前面某点到当前点"的路径和等于 targetSum
        # 原理：如果有 prefix[cur_sum - targetSum] 条路径，减去前缀和，中间段和 = targetSum
        count: int = prefix_count[cur_sum - targetSum]

        # 将当前前缀和加入哈希表，供后续节点使用
        prefix_count[cur_sum] += 1

        # 递归统计左右子树的路径数
        count += dfs(node.left, cur_sum)
        count += dfs(node.right, cur_sum)

        # 回溯：离开当前节点前，将当前前缀和从哈希表中移除
        # 避免影响其他不经过当前节点的路径
        prefix_count[cur_sum] -= 1

        return count

    return dfs(root, 0)


if __name__ == "__main__":
    # 测试1：树 [10,5,-3,3,2,null,11,3,-2,null,1], targetSum=8
    root1 = TreeNode(10)
    root1.left = TreeNode(5)
    root1.right = TreeNode(-3)
    root1.left.left = TreeNode(3)
    root1.left.right = TreeNode(2)
    root1.right.right = TreeNode(11)
    root1.left.left.left = TreeNode(3)
    root1.left.left.right = TreeNode(-2)
    root1.left.right.right = TreeNode(1)
    assert pathSum(root1, 8) == 3  # [5,3], [5,2,1], [-3,11]

    # 测试2：单节点树，正好等于 targetSum
    root2 = TreeNode(1)
    assert pathSum(root2, 1) == 1

    # 测试3：空树
    assert pathSum(None, 0) == 0

    # 测试4：负数和
    root3 = TreeNode(-2)
    root3.right = TreeNode(-3)
    assert pathSum(root3, -5) == 1  # [-2, -3]

    print("所有断言通过！")
