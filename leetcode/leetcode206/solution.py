"""
考点：链表、递归
题目：Reverse Linked List（反转链表）
题目描述：反转一个单链表。
  示例：head = [1,2,3,4,5] → [5,4,3,2,1]
思路：迭代法——pre 指向已反转部分的头部，cur 指向当前节点。
  每次将 cur.next 指向 pre，然后 pre 和 cur 同步前进。
  也可以递归实现，但迭代更省空间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next


def reverseList(head: ListNode | None) -> ListNode | None:
    prev = None  # 已反转部分的头节点（初始为空）
    curr = head  # 尚未反转的当前节点

    while curr:
        # 核心操作：让 curr 指向 prev，实现反转
        next_node = curr.next  # 暂存下一个节点，防止断链
        curr.next = prev  # 反转：当前节点指向前一个节点
        prev = curr  # prev 前进到 curr
        curr = next_node  # curr 前进到下一个节点

    return prev  # 循环结束时 prev 指向原链表的最后一个节点，即新链表头


def build_list(values: list[int]) -> ListNode | None:
    """辅助函数：从数组构建链表"""
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def to_list(head: ListNode | None) -> list[int]:
    """辅助函数：链表转数组"""
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result


if __name__ == "__main__":
    head = build_list([1, 2, 3, 4, 5])
    assert to_list(reverseList(head)) == [5, 4, 3, 2, 1]
    assert reverseList(None) is None
    assert to_list(reverseList(build_list([1]))) == [1]
