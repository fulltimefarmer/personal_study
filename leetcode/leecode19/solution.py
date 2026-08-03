"""
考点：链表、双指针
题目：Remove Nth Node From End of List（删除链表的倒数第 N 个结点）
思路：快慢指针法，快指针先走 n+1 步，然后快慢指针同步移动，当快指针到达末尾时，慢指针在待删除节点的前驱
时间复杂度：O(L)，L 为链表长度
空间复杂度：O(1)
"""
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next

def removeNthFromEnd(head: Optional[ListNode], n: int) -> Optional[ListNode]:
    # 哑节点：统一处理删除头节点的特殊情况
    # dummy.next 始终指向原链表的头节点
    dummy = ListNode(0, head)
    fast: Optional[ListNode] = dummy
    slow: Optional[ListNode] = dummy

    # 第一步：快指针先行 n+1 步
    # 这样当 fast 到达末尾时，slow 正好在倒数第 n+1 个节点（待删除节点的前驱）
    for _ in range(n + 1):
        fast = fast.next  # type: ignore  # fast 初始不为 None

    # 第二步：快慢指针同步移动，直到快指针到达链表末尾
    while fast is not None:
        fast = fast.next
        slow = slow.next  # type: ignore

    # 第三步：删除倒数第 n 个节点
    # slow.next 就是待删除节点，将 next 指向跳过它
    slow.next = slow.next.next  # type: ignore

    return dummy.next  # 返回哑节点的下一个，即可能更新后的头节点

if __name__ == "__main__":
    # 辅助函数
    def build_list(vals: list[int]) -> Optional[ListNode]:
        dummy = ListNode()
        cur = dummy
        for v in vals:
            cur.next = ListNode(v)
            cur = cur.next
        return dummy.next

    def list_to_array(head: Optional[ListNode]) -> list[int]:
        res = []
        while head:
            res.append(head.val)
            head = head.next
        return res

    head = build_list([1, 2, 3, 4, 5])
    assert list_to_array(removeNthFromEnd(head, 2)) == [1, 2, 3, 5]

    head = build_list([1])
    assert list_to_array(removeNthFromEnd(head, 1)) == []

    head = build_list([1, 2])
    assert list_to_array(removeNthFromEnd(head, 1)) == [1]
    print("全部通过 ✓")
