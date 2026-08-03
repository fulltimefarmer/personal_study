"""
考点：Hash Table, Linked List, Two Pointers
题目：Linked List Cycle II（环形链表II）
题目描述：返回链表环的入口节点，无环返回 None。不允许修改链表。
示例 1：head=[3,2,0,-4], pos=1，返回索引为 1 的节点
示例 2：head=[1,2], pos=0，返回索引为 0 的节点
示例 3：head=[1], pos=-1，返回 None
思路：快慢指针检测环 → 相遇后慢指针回头部，同步移动再次相遇即为入口。
Floyd 判环算法：设链表头部到入口距离为 a，入口到相遇点距离为 b，环剩余为 c。
相遇时快指针走了 a+b+n(b+c)，慢指针走了 a+b，2(a+b)=a+b+n(b+c) → a=c+(n-1)(b+c)。
即从头部到入口的距离 a 等于从相遇点走 c 再走若干整圈。
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    def __init__(self, x: int = 0, next: "ListNode | None" = None):
        self.val: int = x
        self.next: ListNode | None = next


def detectCycle(head: ListNode | None) -> ListNode | None:
    slow: ListNode | None = head
    fast: ListNode | None = head

    # 第一轮：快慢指针判环
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            # 有环，将慢指针移到头部，快指针保持在相遇点
            slow = head
            # 第二轮：两者同步走，再次相遇处即为环的入口
            while slow is not fast:
                slow = slow.next
                fast = fast.next
            return slow

    return None


if __name__ == "__main__":
    # [3] → [2] → [0] → [-4] → 回到 [2]
    n1 = ListNode(3)
    n2 = ListNode(2)
    n3 = ListNode(0)
    n4 = ListNode(-4)
    n1.next = n2
    n2.next = n3
    n3.next = n4
    n4.next = n2
    assert detectCycle(n1) is n2

    # 无环链表
    n5 = ListNode(1)
    n5.next = ListNode(2)
    assert detectCycle(n5) is None
