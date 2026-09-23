from typing import List, Optional


class ListNode:
    """单链表节点。"""

    def __init__(self, val: int = 0, next: Optional["ListNode"] = None) -> None:
        self.val = val
        self.next = next


def mergeKLists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """合并 k 个升序链表，返回合并后的升序链表。"""
    pass
