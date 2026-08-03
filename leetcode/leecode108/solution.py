"""
考点：Tree, BST, Divide and Conquer, Binary Tree
题目：Convert Sorted Array to Binary Search Tree（将有序数组转换为二叉搜索树）
题目描述：将一个按照升序排列的有序数组，转换为一棵高度平衡的二叉搜索树。
"高度平衡" 二叉树是指每个节点的左右两个子树的高度差的绝对值不超过 1。
示例 1：输入 nums = [-10,-3,0,5,9]，输出 [0,-3,9,-10,None,5]
示例 2：输入 nums = [1,3]，输出 [3,1]
思路：每次选取数组中间元素作为根节点，递归构建左右子树。
时间复杂度：O(n)
空间复杂度：O(log n)
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def sortedArrayToBST(nums: list[int]) -> TreeNode | None:
    def helper(left: int, right: int) -> TreeNode | None:
        # 区间为空时返回 None，作为叶子节点的子节点
        if left > right:
            return None
        # 取中间元素作为根节点，保证高度平衡
        mid: int = (left + right) // 2  # Python 的 // 是整除（向下取整）
        root: TreeNode = TreeNode(nums[mid])
        # 左子树由左半部分构建
        root.left = helper(left, mid - 1)
        # 右子树由右半部分构建
        root.right = helper(mid + 1, right)
        return root

    return helper(0, len(nums) - 1)


if __name__ == "__main__":
    # [-10, -3, 0, 5, 9] → 高度平衡 BST
    root = sortedArrayToBST([-10, -3, 0, 5, 9])
    assert root is not None and root.val == 0
    assert root.left.val == -10
    assert root.left.right.val == -3
    assert root.right.val == 5
    assert root.right.right.val == 9
    # 空数组
    assert sortedArrayToBST([]) is None
