"""
考点：递归、链表
题目：Reverse Linked List（反转链表）
思路：迭代法，pre/cur/next 三指针，cur.next=pre 逐个反转。
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    """单链表节点定义"""

    def __init__(self, val: int = 0, next_: "ListNode | None" = None):
        self.val = val
        self.next = next_


def reverseList(head: ListNode | None) -> ListNode | None:
    prev: ListNode | None = None  # 已反转部分的头节点
    cur: ListNode | None = head   # 当前处理的节点

    while cur is not None:
        # 保存下一个节点，防止断链
        nxt = cur.next
        # 反转当前节点的指向
        cur.next = prev
        # prev 和 cur 同时前移
        prev = cur
        cur = nxt

    return prev  # 反转后 prev 即为新头节点


def _list_to_nodes(nums: list[int]) -> ListNode | None:
    """辅助函数：将列表转为链表"""
    if not nums:
        return None
    head = ListNode(nums[0])
    cur = head
    for i in range(1, len(nums)):
        cur.next = ListNode(nums[i])
        cur = cur.next
    return head


def _nodes_to_list(head: ListNode | None) -> list[int]:
    """辅助函数：将链表转为列表"""
    result: list[int] = []
    cur = head
    while cur:
        result.append(cur.val)
        cur = cur.next
    return result


if __name__ == "__main__":
    # 示例: [1,2,3,4,5] → [5,4,3,2,1]
    head = _list_to_nodes([1, 2, 3, 4, 5])
    reversed_head = reverseList(head)
    assert _nodes_to_list(reversed_head) == [5, 4, 3, 2, 1]
    # 空链表
    assert reverseList(None) is None
    print("全部测试通过")
