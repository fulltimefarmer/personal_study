"""
考点：Tree, BFS, Binary Tree
题目：Binary Tree Level Order Traversal（二叉树的层序遍历）
题目描述：给定二叉树根节点，返回层序遍历结果（按层分组，从左到右）。
示例：root = [3,9,20,None,None,15,7] → [[3],[9,20],[15,7]]
思路：BFS 队列。记录每层节点数 level_size，依次处理该层所有节点，子节点入队。
时间复杂度：O(n)
空间复杂度：O(n)
"""
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def levelOrder(root: TreeNode | None) -> list[list[int]]:
    if not root:
        return []

    result: list[list[int]] = []
    # 使用 collections.deque 作为队列，popleft() 比 list.pop(0) 效率高 O(1) vs O(n)
    queue: deque[TreeNode] = deque([root])

    while queue:
        # 当前层的节点数，必须在遍历前固定，因为遍历过程中队列会增长
        level_size: int = len(queue)
        level: list[int] = []

        for _ in range(level_size):
            # popleft() 从队列左侧取出节点，等价于 JS 中的 shift()
            node: TreeNode = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        result.append(level)

    return result


if __name__ == "__main__":
    # 构造示例树：[3,9,20,None,None,15,7] → [[3],[9,20],[15,7]]
    root = TreeNode(3)
    root.left = TreeNode(9)
    root.right = TreeNode(20)
    root.right.left = TreeNode(15)
    root.right.right = TreeNode(7)
    assert levelOrder(root) == [[3], [9, 20], [15, 7]]
    # 空树测试
    assert levelOrder(None) == []
