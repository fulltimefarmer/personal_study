"""
考点：栈、树、设计、二叉搜索树、二叉树、迭代器
题目：Binary Search Tree Iterator（二叉搜索树迭代器）
思路：用栈模拟中序遍历。初始化时沿左子树压栈，next() 弹出栈顶并处理其右子树的左链。
      均摊 O(1)，空间 O(h)。
时间复杂度：均摊 O(1)
空间复杂度：O(h)，h 为树高
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


class BSTIterator:
    """二叉搜索树中序迭代器"""

    def __init__(self, root: TreeNode | None):
        self.stack: list[TreeNode] = []  # 用列表模拟栈
        self._push_left(root)  # 初始化时沿左子树一路压栈

    def _push_left(self, node: TreeNode | None) -> None:
        """将 node 及其所有左子节点压入栈中"""
        while node is not None:
            self.stack.append(node)
            node = node.left

    def next(self) -> int:
        # 弹出栈顶元素（当前中序最小值）
        node = self.stack.pop()
        # 处理弹出节点的右子树左链，为后续 next 做准备
        self._push_left(node.right)
        return node.val

    def hasNext(self) -> bool:
        return len(self.stack) > 0


if __name__ == "__main__":
    # 构建 BST: [7, 3, 15, None, None, 9, 20]
    #          7
    #        /   \
    #       3     15
    #            /  \
    #           9   20
    root = TreeNode(7)
    root.left = TreeNode(3)
    root.right = TreeNode(15)
    root.right.left = TreeNode(9)
    root.right.right = TreeNode(20)

    it = BSTIterator(root)
    assert it.next() == 3  # 最小元素
    assert it.next() == 7
    assert it.hasNext() is True
    assert it.next() == 9
    assert it.hasNext() is True
    assert it.next() == 15
    assert it.next() == 20
    assert it.hasNext() is False
    print("全部测试通过")
