"""
考点：树、深度优先搜索、广度优先搜索、二叉树
题目：Invert Binary Tree（翻转二叉树）
题目描述：翻转二叉树，即左右子树互换。
  示例：root = [4,2,7,1,3,6,9] → [4,7,2,9,6,3,1]
思路：递归。交换左右子树，然后分别递归翻转左子树和右子树。
时间复杂度：O(n)
空间复杂度：O(h)（h 为树高，递归栈深度）
"""


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def invertTree(root: TreeNode | None) -> TreeNode | None:
    if root is None:
        return None

    # 核心操作：交换当前节点的左右子树
    root.left, root.right = root.right, root.left
    # Python 多变量同时赋值特性：右边先计算，左边一次性赋值，无需临时变量

    # 递归翻转子树的子树
    invertTree(root.left)
    invertTree(root.right)

    return root


def build_tree(values: list[int | None]) -> TreeNode | None:
    """从层序遍历列表构建二叉树（None 表示空节点）"""
    if not values or values[0] is None:
        return None
    from collections import deque
    root = TreeNode(values[0])
    q: deque[TreeNode | None] = deque([root])
    i = 1
    while q and i < len(values):
        node = q.popleft()
        if node:
            if i < len(values) and values[i] is not None:
                node.left = TreeNode(values[i])
                q.append(node.left)
            i += 1
            if i < len(values) and values[i] is not None:
                node.right = TreeNode(values[i])
                q.append(node.right)
            i += 1
    return root


def to_list(root: TreeNode | None) -> list[int | None]:
    """二叉树转层序遍历列表"""
    if not root:
        return []
    result: list[int | None] = []
    from collections import deque
    q: deque[TreeNode | None] = deque([root])
    while q:
        node = q.popleft()
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
    root = build_tree([4, 2, 7, 1, 3, 6, 9])
    inverted = invertTree(root)
    assert to_list(inverted) == [4, 7, 2, 9, 6, 3, 1]
    assert invertTree(None) is None
