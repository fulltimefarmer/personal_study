"""
考点：树、DFS、BFS、二叉树
题目：Invert Binary Tree（翻转二叉树）
思路：递归，翻转左右子树后交换当前节点的左右孩子。
时间复杂度：O(n)
空间复杂度：O(h)，h 为树高（递归栈），最坏 O(n)
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def invertTree(root: TreeNode | None) -> TreeNode | None:
    if root is None:
        return None

    # 递归翻转左右子树
    left = invertTree(root.left)
    right = invertTree(root.right)

    # 交换当前节点的左右子树
    root.left = right
    root.right = left

    return root


def _tree_to_level_order(root: TreeNode | None) -> list[int | None]:
    """辅助函数：层序遍历转为列表（方便测试验证）"""
    if root is None:
        return []
    result: list[int | None] = []
    q = [root]
    while q:
        node = q.pop(0)
        if node:
            result.append(node.val)
            q.append(node.left)
            q.append(node.right)
        else:
            result.append(None)
    # 去掉末尾的 None
    while result and result[-1] is None:
        result.pop()
    return result


if __name__ == "__main__":
    # 构建树: [4,2,7,1,3,6,9]
    root = TreeNode(4)
    root.left = TreeNode(2, TreeNode(1), TreeNode(3))
    root.right = TreeNode(7, TreeNode(6), TreeNode(9))
    # 翻转后: [4,7,2,9,6,3,1]
    inverted = invertTree(root)
    assert _tree_to_level_order(inverted) == [4, 7, 2, 9, 6, 3, 1]
    # 空树
    assert invertTree(None) is None
    print("全部测试通过")
