"""
考点：链表、递归
题目：Merge Two Sorted Lists（合并两个有序链表）
思路：迭代法，比较两个链表当前节点的值，将较小值接入结果链表，直到一个链表为空时拼接剩余部分
时间复杂度：O(m + n)
空间复杂度：O(1)
"""
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next

def mergeTwoLists(
    list1: Optional[ListNode], list2: Optional[ListNode]
) -> Optional[ListNode]:
    # 哑节点技巧：避免处理结果链表为空时的特殊情况
    dummy = ListNode(0)
    curr = dummy  # curr 始终指向结果链表的最后一个节点

    # 当两个链表都有节点时，比较并连接较小的
    while list1 is not None and list2 is not None:
        if list1.val <= list2.val:
            curr.next = list1  # 将 list1 的当前节点接入结果链表
            list1 = list1.next  # 移动 list1 的指针
        else:
            curr.next = list2  # 将 list2 的当前节点接入结果链表
            list2 = list2.next  # 移动 list2 的指针
        curr = curr.next  # 移动结果链表的指针到末尾

    # 拼接剩余的链表（至多有一个链表非空）
    # Python 的 or 短路求值：如果 list1 为 None 则取 list2
    curr.next = list1 if list1 is not None else list2

    return dummy.next  # 返回哑节点的下一个，即真正的合并结果头节点

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

    l1 = build_list([1, 2, 4])
    l2 = build_list([1, 3, 4])
    assert list_to_array(mergeTwoLists(l1, l2)) == [1, 1, 2, 3, 4, 4]

    assert list_to_array(mergeTwoLists(None, None)) == []
    assert list_to_array(mergeTwoLists(None, build_list([0]))) == [0]
    print("全部通过 ✓")
