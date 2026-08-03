"""
考点：链表、分治、堆
题目：Merge k Sorted Lists（合并 K 个升序链表）
思路：分治法，递归地将 k 个链表两两配对合并，每次合并两个有序链表，时间复杂度从 O(kN) 优化到 O(N log k)
时间复杂度：O(N log k)，N 为总节点数
空间复杂度：O(log k)，递归栈深度
"""
from typing import Optional, List

class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next

def mergeKLists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    if not lists:  # 空列表直接返回 None
        return None
    return mergeRange(lists, 0, len(lists) - 1)

def mergeRange(
    lists: List[Optional[ListNode]], left: int, right: int
) -> Optional[ListNode]:
    """分治：递归地将 [left, right] 区间内的链表合并为一个"""
    if left == right:
        return lists[left]  # 区间只有一个链表，直接返回

    # 计算中间位置，>> 1 等价于 // 2（位运算更快）
    mid = (left + right) >> 1
    # 递归地合并左半部分和右半部分
    l1 = mergeRange(lists, left, mid)
    l2 = mergeRange(lists, mid + 1, right)

    return mergeTwoLists(l1, l2)  # 合并两个有序链表

def mergeTwoLists(
    l1: Optional[ListNode], l2: Optional[ListNode]
) -> Optional[ListNode]:
    """合并两个有序链表的辅助函数（同 LeetCode 21）"""
    dummy = ListNode(0)
    curr = dummy

    while l1 is not None and l2 is not None:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next

    # 拼接剩余部分
    curr.next = l1 if l1 is not None else l2
    return dummy.next

if __name__ == "__main__":
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

    lists = [
        build_list([1, 4, 5]),
        build_list([1, 3, 4]),
        build_list([2, 6]),
    ]
    assert list_to_array(mergeKLists(lists)) == [1, 1, 2, 3, 4, 4, 5, 6]

    assert mergeKLists([]) is None
    assert list_to_array(mergeKLists([None])) == []
    print("全部通过 ✓")
