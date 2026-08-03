"""
考点：树、DFS、设计、字符串、二叉树
题目：Serialize and Deserialize Binary Tree（二叉树的序列化与反序列化）—— LeetCode 297
题目描述：设计算法将二叉树序列化为字符串并能反序列化还原
思路：前序遍历 DFS。序列化时用 "null" 标记空节点，逗号分隔。
      反序列化时递归按前序构建，遇到 "null" 返回 None。
时间复杂度：O(n)
空间复杂度：O(n)
"""

from __future__ import annotations


class TreeNode:
    """二叉树节点定义"""

    def __init__(self, val: int = 0, left: TreeNode | None = None, right: TreeNode | None = None) -> None:
        self.val: int = val
        self.left: TreeNode | None = left
        self.right: TreeNode | None = right


def serialize(root: TreeNode | None) -> str:
    """将二叉树序列化为字符串，前序遍历，空节点用 'null' 表示"""
    result: list[str] = []

    def dfs(node: TreeNode | None) -> None:
        # 嵌套函数：前序遍历，将节点值转为字符串存入列表
        if node is None:
            result.append("null")
            return
        result.append(str(node.val))  # 先访问根
        dfs(node.left)   # 再递归左子树
        dfs(node.right)  # 最后递归右子树

    dfs(root)
    # str.join(iterable)：用指定的分隔符拼接可迭代对象中的所有字符串
    return ",".join(result)


def deserialize(data: str) -> TreeNode | None:
    """将字符串反序列化还原为二叉树"""
    # str.split(sep)：按分隔符切分字符串，返回字符串列表
    nodes: list[str] = data.split(",")
    # 使用列表包装索引，使嵌套函数可以修改它（整数不可变，需通过列表引用）
    # Python 中 nonlocal 声明也可以实现，但用列表更直观地共享状态
    index = 0

    def dfs() -> TreeNode | None:
        nonlocal index
        if nodes[index] == "null":
            index += 1
            return None
        # 创建当前节点，值需要从字符串转为整数
        node = TreeNode(int(nodes[index]))
        index += 1
        # 按前序递归构建左右子树
        node.left = dfs()
        node.right = dfs()
        return node

    return dfs()


if __name__ == "__main__":
    # 构建测试树：    1
    #              /   \
    #             2     3
    #            / \   / \
    #          null null 4   5
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.right.left = TreeNode(4)
    root.right.right = TreeNode(5)

    data = serialize(root)
    assert data == "1,2,null,null,3,4,null,null,5,null,null"

    restored = deserialize(data)
    assert restored is not None
    assert restored.val == 1
    assert restored.left is not None and restored.left.val == 2
    assert restored.right is not None and restored.right.val == 3

    # 空树测试
    assert serialize(None) == "null"
    assert deserialize("null") is None

    print("所有断言通过！")
