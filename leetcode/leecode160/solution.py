"""
考点：Hash Table, Linked List, Two Pointers
题目：Intersection of Two Linked Lists（相交链表）
题目描述：找两个链表的相交起始节点，不相交返回 None。链表无环。
示例 1：listA=[4,1,8,4,5], listB=[5,6,1,8,4,5]，相交于节点 8
示例 2：listA=[1,9,1,2,4], listB=[3,2,4]，相交于节点 2
示例 3：listA=[2,6,4], listB=[1,5]，无相交
思路：双指针，各走完整链表后切换到对方头部。有交点则相遇，无交点则同时到 None。
路径：pA: a+c+b, pB: b+c+a，两者相等（a、b 为各自独立部分，c 为公共部分）。
时间复杂度：O(m+n)
空间复杂度：O(1)
"""


class ListNode:
    def __init__(self, x: int = 0, next: "ListNode | None" = None):
        self.val: int = x
        self.next: ListNode | None = next


def getIntersectionNode(headA: ListNode | None, headB: ListNode | None) -> ListNode | None:
    pA: ListNode | None = headA
    pB: ListNode | None = headB

    # 当两个指针相同时返回（都指向交点，或者都指向 None）
    while pA is not pB:
        # 三目表达式：如果 pA 走到末尾就切换到 headB，否则继续走
        pA = headB if pA is None else pA.next
        pB = headA if pB is None else pB.next

    return pA


if __name__ == "__main__":
    # listA=[4,1,8,4,5], listB=[5,6,1,8,4,5]，相交于 8
    c1 = ListNode(8)
    c2 = ListNode(4)
    c3 = ListNode(5)
    c1.next = c2
    c2.next = c3

    a1 = ListNode(4)
    a2 = ListNode(1)
    a1.next = a2
    a2.next = c1

    b1 = ListNode(5)
    b2 = ListNode(6)
    b3 = ListNode(1)
    b1.next = b2
    b2.next = b3
    b3.next = c1

    assert getIntersectionNode(a1, b1) is c1

    # 不相交
    x1 = ListNode(2)
    x2 = ListNode(6)
    x3 = ListNode(4)
    x1.next = x2
    x2.next = x3

    y1 = ListNode(1)
    y2 = ListNode(5)
    y1.next = y2

    assert getIntersectionNode(x1, y1) is None
