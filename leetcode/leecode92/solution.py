"""
考点: Linked List
题目: Reverse Linked List II（反转链表 II）
题目描述: 反转链表从 left 到 right 位置的节点（1-indexed）。
示例: head = [1,2,3,4,5], left = 2, right = 4 -> [1,4,3,2,5]
思路: 哑节点 + 头插法。找到 left 前驱 prev，对区间内每个节点，
      将其从链表中断开并头插到 prev 后面。
时间复杂度: O(n)
空间复杂度: O(1)
"""

from __future__ import annotations


class ListNode:
    """单链表节点"""
    def __init__(self, val: int = 0, next: ListNode | None = None):
        self.val = val
        self.next = next


def reverseBetween(head: ListNode | None, left: int, right: int) -> ListNode | None:
    if not head:
        return None

    # 哑节点: 简化边界处理，当 left=1 时 prev 不会为 None
    # dummy.next 始终指向链表真正的头
    dummy = ListNode(0, head)
    prev = dummy

    # 移动 prev 到 left 位置的前一个节点
    for _ in range(left - 1):
        prev = prev.next  # 保证非 None，因为 left 在有效范围内

    # curr 始终指向原反转区间的第一个节点（在反转过程中它会被逐步挤到后面）
    curr = prev.next

    # 头插法: 将 curr 后面的节点依次移到 prev 后面（即区间开头）
    # 需要交换 (right - left) 次
    # 例: 1->[2->3->4]->5, left=2, right=4
    #     第1次: 1->3->2->4->5  (将 3 插入到 2 前面)
    #     第2次: 1->4->3->2->5  (将 4 插入到 3 前面)
    for _ in range(right - left):
        # next_node 是要移到前面的节点
        next_node = curr.next
        # 从链表中取出 next_node
        curr.next = next_node.next
        # 将 next_node 插入到 prev 后面（成为区间新头部）
        next_node.next = prev.next
        prev.next = next_node

    return dummy.next


def list_to_nodes(vals: list[int]) -> ListNode | None:
    """辅助函数: 将列表转换为链表"""
    dummy = ListNode()
    curr = dummy
    for v in vals:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def nodes_to_list(head: ListNode | None) -> list[int]:
    """辅助函数: 将链表转换为列表"""
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result


if __name__ == "__main__":
    head1 = list_to_nodes([1, 2, 3, 4, 5])
    result1 = reverseBetween(head1, 2, 4)
    assert nodes_to_list(result1) == [1, 4, 3, 2, 5]

    head2 = list_to_nodes([5])
    result2 = reverseBetween(head2, 1, 1)
    assert nodes_to_list(result2) == [5]

    head3 = list_to_nodes([1, 2, 3, 4, 5])
    result3 = reverseBetween(head3, 1, 5)
    assert nodes_to_list(result3) == [5, 4, 3, 2, 1]
