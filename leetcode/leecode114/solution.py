"""
考点：Stack, Tree, DFS, Linked List, Binary Tree
题目：Flatten Binary Tree to Linked List（二叉树展开为链表）
题目描述：将二叉树原地展开为一个单链表，展开后的单链表应该与二叉树先序遍历顺序相同，右指针指向链表下一个节点，左指针始终为 None。
示例 1：root = [1,2,5,3,4,None,6]，输出 [1,None,2,None,3,None,4,None,5,None,6]
示例 2：root = []，输出 []
示例 3：root = [0]，输出 [0]
思路：逆先序遍历（右-左-根），维护 prev 指针，将当前节点右指针指向 prev，左指针置 None。
时间复杂度：O(n)
空间复杂度：O(h)
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def flatten(root: TreeNode | None) -> None:
    # 使用 nonlocal 让内部函数可以修改外层变量 prev
    prev: TreeNode | None = None

    def dfs(node: TreeNode | None) -> None:
        nonlocal prev  # Python 闭包中修改外部变量必须声明 nonlocal
        if node is None:
            return
        # 逆先序遍历：右 → 左 → 根（正常先序是根→左→右，逆序就是右→左→根）
        dfs(node.right)
        dfs(node.left)
        # 将当前节点的右指针指向前一个处理过的节点（prev）
        node.right = prev
        node.left = None
        # 更新 prev 为当前节点
        prev = node

    dfs(root)


if __name__ == "__main__":
    # [1,2,5,3,4,None,6] → [1,None,2,None,3,None,4,None,5,None,6]
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(5)
    root.left.left = TreeNode(3)
    root.left.right = TreeNode(4)
    root.right.right = TreeNode(6)
    flatten(root)
    # 验证：沿着右指针遍历，值应该是 1,2,3,4,5,6
    vals = []
    while root:
        vals.append(root.val)
        assert root.left is None
        root = root.right
    assert vals == [1, 2, 3, 4, 5, 6]
