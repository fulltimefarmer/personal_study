"""
考点：栈、树、设计、迭代器
题目：Binary Search Tree Iterator（二叉搜索树迭代器）
题目描述：实现一个二叉搜索树中序遍历迭代器。
  要求：next() 和 hasNext() 均摊时间复杂度 O(1)，空间复杂度 O(h)（h 为树高）。
思路：用栈模拟中序遍历。初始化时把根节点到最左节点的路径全部压栈。
  next() 弹出栈顶节点，返回其值，然后将其右子树的最左路径压栈。
  hasNext() 判断栈是否非空。
时间复杂度：next() 均摊 O(1)，hasNext() O(1)
空间复杂度：O(h)
"""


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


class BSTIterator:
    def __init__(self, root: TreeNode | None):
        self.stack: list[TreeNode] = []
        self._push_left(root)  # 初始化：将根到最左节点路径全部压栈

    def _push_left(self, node: TreeNode | None) -> None:
        """将 node 及其所有左子节点依次压入栈中"""
        while node:
            self.stack.append(node)
            node = node.left

    def next(self) -> int:
        # 弹出栈顶节点（当前中序遍历的节点）
        node = self.stack.pop()
        # 如果该节点有右子树，将右子树的最左路径压栈
        # 这样下一次 next() 就会按中序顺序访问右子树的最小节点
        self._push_left(node.right)
        return node.val

    def hasNext(self) -> bool:
        return len(self.stack) > 0  # 栈非空说明还有未访问的节点


if __name__ == "__main__":
    # 构建 BST:
    #       7
    #      / \
    #     3   15
    #        /  \
    #       9    20
    root = TreeNode(7)
    root.left = TreeNode(3)
    root.right = TreeNode(15)
    root.right.left = TreeNode(9)
    root.right.right = TreeNode(20)

    it = BSTIterator(root)
    results = []
    while it.hasNext():
        results.append(it.next())
    assert results == [3, 7, 9, 15, 20]  # 中序遍历结果
