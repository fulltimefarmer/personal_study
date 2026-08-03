"""
考点：Tree, Array, Hash Table, Divide and Conquer, Binary Tree
题目：Construct Binary Tree from Preorder and Inorder Traversal（从前序与中序遍历序列构造二叉树）
题目描述：给定前序遍历 preorder 和中序遍历 inorder，构造并返回二叉树根节点。
示例：preorder = [3,9,20,15,7], inorder = [9,3,15,20,7] → [3,9,20,None,None,15,7]
思路：递归分治。前序首元素为根，在中序中找到根位置，左侧为左子树，右侧为右子树。
      哈希表快速定位中序中的根索引，根据左子树大小切分前序数组，递归构造。
时间复杂度：O(n)
空间复杂度：O(n)
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def buildTree(preorder: list[int], inorder: list[int]) -> TreeNode | None:
    # 构建中序遍历值→索引的哈希表，O(1) 定位根节点在中序中的位置
    inorder_map: dict[int, int] = {val: idx for idx, val in enumerate(inorder)}

    def build(pre_start: int, pre_end: int, in_start: int, in_end: int) -> TreeNode | None:
        # 递归终止条件：前序区间为空
        if pre_start > pre_end:
            return None

        # 前序遍历的第一个元素就是当前子树的根节点
        root_val: int = preorder[pre_start]
        root: TreeNode = TreeNode(root_val)
        # 根节点在中序遍历中的索引
        root_idx: int = inorder_map[root_val]
        # 左子树的节点数量 = 根位置 - 中序起始位置
        left_size: int = root_idx - in_start

        # 前序左子树区间：[pre_start+1, pre_start+left_size]
        # 中序左子树区间：[in_start, root_idx-1]
        root.left = build(pre_start + 1, pre_start + left_size, in_start, root_idx - 1)
        # 前序右子树区间：[pre_start+left_size+1, pre_end]
        # 中序右子树区间：[root_idx+1, in_end]
        root.right = build(pre_start + left_size + 1, pre_end, root_idx + 1, in_end)

        return root

    return build(0, len(preorder) - 1, 0, len(inorder) - 1)


if __name__ == "__main__":
    # 构造示例
    root = buildTree([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])
    assert root is not None and root.val == 3
    assert root.left.val == 9
    assert root.right.val == 20
    assert root.right.left.val == 15
    assert root.right.right.val == 7
    assert buildTree([], []) is None
