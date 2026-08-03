"""
考点：Linked List, Two Pointers, Divide and Conquer, Sorting, Merge Sort
题目：Sort List（排序链表）
题目描述：对链表进行升序排序，O(n log n) 时间，O(1) 空间（进阶）。
示例 1：[4,2,1,3]，输出 [1,2,3,4]
示例 2：[-1,5,3,4,0]，输出 [-1,0,3,4,5]
示例 3：[]，输出 []
思路：归并排序。快慢指针找中点，递归排序左右，合并有序链表。
时间复杂度：O(n log n)
空间复杂度：O(log n)（递归栈）
"""


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val: int = val
        self.next: ListNode | None = next


def sortList(head: ListNode | None) -> ListNode | None:
    # 递归终止条件：空链表或单节点链表已有序
    if head is None or head.next is None:
        return head

    # 快慢指针找链表中点：慢指针每次一步，快指针每次两步
    # 快指针初始化为 head.next 可保证慢指针落在中点的前一个（偏左）
    slow: ListNode | None = head
    fast: ListNode | None = head.next

    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next

    # 断开链表：mid 是右半部分的头节点
    mid: ListNode | None = slow.next
    slow.next = None

    # 递归分别排序左右两半
    left: ListNode | None = sortList(head)
    right: ListNode | None = sortList(mid)

    # 合并两个有序链表
    return _merge(left, right)


def _merge(l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
    """合并两个有序链表，返回合并后的头节点"""
    dummy: ListNode = ListNode(0)  # 虚拟头节点，简化边界处理
    curr: ListNode = dummy

    while l1 is not None and l2 is not None:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next

    # 将剩余部分直接接上
    curr.next = l1 if l1 is not None else l2
    return dummy.next


if __name__ == "__main__":
    # 构造 [4,2,1,3] → [1,2,3,4]
    def build_list(vals: list[int]) -> ListNode | None:
        if not vals:
            return None
        head = ListNode(vals[0])
        curr = head
        for v in vals[1:]:
            curr.next = ListNode(v)
            curr = curr.next
        return head

    def to_list(head: ListNode | None) -> list[int]:
        result = []
        while head:
            result.append(head.val)
            head = head.next
        return result

    head = build_list([4, 2, 1, 3])
    assert to_list(sortList(head)) == [1, 2, 3, 4]

    head2 = build_list([-1, 5, 3, 4, 0])
    assert to_list(sortList(head2)) == [-1, 0, 3, 4, 5]

    assert sortList(None) is None
