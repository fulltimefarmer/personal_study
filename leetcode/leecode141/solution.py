"""
考点：Hash Table, Linked List, Two Pointers
题目：Linked List Cycle（环形链表）
题目描述：判断链表是否有环。
示例 1：head=[3,2,0,-4], pos=1，输出 true
示例 2：head=[1,2], pos=0，输出 true
示例 3：head=[1], pos=-1，输出 false
思路：快慢指针，快指针每次两步，慢指针一步。有环则相遇，无环则快指针先到 None。
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    def __init__(self, x: int = 0, next: "ListNode | None" = None):
        self.val: int = x
        self.next: ListNode | None = next


def hasCycle(head: ListNode | None) -> bool:
    slow: ListNode | None = head
    fast: ListNode | None = head

    # 快指针每次走两步，需要检查当前和下一位是否为空
    while fast is not None and fast.next is not None:
        slow = slow.next          # 慢指针走一步
        fast = fast.next.next     # 快指针走两步
        if slow is fast:          # is 比较对象身份，有环必然相遇
            return True

    return False


if __name__ == "__main__":
    # 有环链表：[3] → [2] → [0] → [-4] → 回到 [2]
    n1 = ListNode(3)
    n2 = ListNode(2)
    n3 = ListNode(0)
    n4 = ListNode(-4)
    n1.next = n2
    n2.next = n3
    n3.next = n4
    n4.next = n2
    assert hasCycle(n1) is True

    # 无环链表：[1] → [2]
    n5 = ListNode(1)
    n5.next = ListNode(2)
    assert hasCycle(n5) is False

    assert hasCycle(None) is False
