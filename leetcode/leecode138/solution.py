"""
考点：Hash Table, Linked List
题目：Copy List with Random Pointer（随机链表的复制）
题目描述：深拷贝带随机指针的链表。新节点值相同，next 和 random 指向复制链表中对应的新节点。
示例：head = [[7,None],[13,0],[11,4],[10,2],[1,0]]，输出同样的结构。
思路：HashMap 存储原节点→新节点的映射，两遍遍历建立 next 和 random 关系。
时间复杂度：O(n)
空间复杂度：O(n)
"""


class Node:
    def __init__(self, x: int = 0, next: "Node | None" = None, random: "Node | None" = None):
        self.val: int = x
        self.next: Node | None = next
        self.random: Node | None = random


def copyRandomList(head: Node | None) -> Node | None:
    if head is None:
        return None

    # 哈希表：原节点 → 新节点的映射
    # dict 是 Python 的哈希表实现，O(1) 查找
    node_map: dict[Node, Node] = {}

    # 第一遍遍历：创建所有新节点，只拷贝 val
    curr: Node | None = head
    while curr:
        node_map[curr] = Node(curr.val)
        curr = curr.next

    # 第二遍遍历：建立新节点之间的 next 和 random 关系
    curr = head
    while curr:
        copy: Node = node_map[curr]
        # 注意：dict.get(key) 返回 None 如果 key 不存在，这正好对应链表末尾
        copy.next = node_map.get(curr.next)  # type: ignore
        copy.random = node_map.get(curr.random)  # type: ignore
        curr = curr.next

    return node_map[head]


if __name__ == "__main__":
    # 构造 [[7,None],[13,0],[11,4],[10,2],[1,0]]
    n0 = Node(7)
    n1 = Node(13)
    n2 = Node(11)
    n3 = Node(10)
    n4 = Node(1)
    n0.next = n1
    n1.next = n2
    n2.next = n3
    n3.next = n4
    n1.random = n0
    n2.random = n4
    n3.random = n2
    n4.random = n0

    copied = copyRandomList(n0)
    assert copied is not None and copied.val == 7
    assert copied.next and copied.next.val == 13
    assert copied.next.random is copied
    assert copied.random is None
