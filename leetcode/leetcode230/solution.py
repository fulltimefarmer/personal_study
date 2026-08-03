"""
考点：树、深度优先搜索、二叉搜索树
题目：Kth Smallest Element in a BST（二叉搜索树中第K小的元素）
题目描述：找出二叉搜索树中第 k 小的元素。
  示例：root = [3,1,4,null,2], k = 1 → 1
思路：BST 的中序遍历是递增序列。进行中序遍历，遍历到第 k 个节点时返回其值。
  迭代法（栈）更直观，无需维护全局计数。
时间复杂度：O(h + k)（h 为树高）
空间复杂度：O(h)
"""


class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None):
        self.val = val
        self.left = left
        self.right = right


def kthSmallest(root: TreeNode | None, k: int) -> int:
    # 迭代中序遍历：利用 BST 中序递增的性质
    stack: list[TreeNode] = []
    curr = root

    while stack or curr:
        # 一路向左，将左子节点全部压栈
        while curr:
            stack.append(curr)
            curr = curr.left

        # 弹出栈顶访问
        curr = stack.pop()
        k -= 1  # 访问了当前节点，k 减 1
        if k == 0:
            return curr.val  # 第 k 个节点，直接返回

        # 转向右子树继续中序遍历
        curr = curr.right

    # 题目保证 k 有效，不会走到这里
    return -1


if __name__ == "__main__":
    #      3
    #     / \
    #    1   4
    #     \
    #      2
    root = TreeNode(3)
    root.left = TreeNode(1)
    root.right = TreeNode(4)
    root.left.right = TreeNode(2)

    assert kthSmallest(root, 1) == 1
    assert kthSmallest(root, 3) == 3
    assert kthSmallest(root, 4) == 4
