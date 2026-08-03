"""
考点：树、DFS、二叉搜索树、二叉树
题目：Kth Smallest Element in a BST（二叉搜索树中第 K 小的元素）
思路：迭代中序遍历（栈），到第 k 个出队元素时返回，中断遍历。
时间复杂度：O(h + k)，h 为树高
空间复杂度：O(h)
"""


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def kthSmallest(root: TreeNode | None, k: int) -> int:
    # 用列表模拟栈，实现迭代式中序遍历
    stack: list[TreeNode] = []
    node = root

    while True:
        # 沿左子树一路压栈（找最小值方向）
        while node is not None:
            stack.append(node)
            node = node.left

        # 弹出栈顶元素（当前中序下一个元素）
        node = stack.pop()
        k -= 1
        # 找到第 k 小元素
        if k == 0:
            return node.val

        # 处理右子树
        node = node.right


if __name__ == "__main__":
    # 构建 BST: [3,1,4,None,2]
    root = TreeNode(3)
    root.left = TreeNode(1, None, TreeNode(2))
    root.right = TreeNode(4)
    # k=1 → 最小元素 1
    assert kthSmallest(root, 1) == 1
    # k=3 → 3
    assert kthSmallest(root, 3) == 3
    print("全部测试通过")
