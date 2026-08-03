"""
考点：栈、递归、链表、双指针
题目：Palindrome Linked List（回文链表）
思路：快慢指针找中点，反转后半部分，前后比较。O(n) 时间 O(1) 空间。
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    """单链表节点定义"""

    def __init__(self, val: int = 0, next_: "ListNode | None" = None):
        self.val = val
        self.next = next_


def isPalindrome(head: ListNode | None) -> bool:
    if head is None or head.next is None:
        return True  # 空链表或单节点链表必为回文

    # 第一步：快慢指针找链表中点
    slow: ListNode | None = head
    fast: ListNode | None = head
    while fast is not None and fast.next is not None:
        slow = slow.next          # type: ignore[union-attr]  # 慢指针走一步
        fast = fast.next.next     # 快指针走两步

    # 第二步：反转后半部分链表
    prev: ListNode | None = None
    while slow is not None:
        nxt = slow.next           # 保存下一个节点
        slow.next = prev          # 反转指针
        prev = slow               # prev 前移
        slow = nxt                # slow 前移
    # prev 现在指向反转后的后半部分头节点

    # 第三步：前后两部分比较
    left: ListNode | None = head
    right: ListNode | None = prev
    while right is not None:
        if left.val != right.val:  # type: ignore[union-attr]  # left 一定非空
            return False
        left = left.next           # type: ignore[union-attr]
        right = right.next

    return True


def _list_to_nodes(nums: list[int]) -> ListNode | None:
    if not nums:
        return None
    head = ListNode(nums[0])
    cur = head
    for i in range(1, len(nums)):
        cur.next = ListNode(nums[i])
        cur = cur.next
    return head


if __name__ == "__main__":
    # 示例 1: [1,2,2,1] → true
    assert isPalindrome(_list_to_nodes([1, 2, 2, 1])) is True
    # 示例 2: [1,2] → false
    assert isPalindrome(_list_to_nodes([1, 2])) is False
    # 示例 3: [1] → true
    assert isPalindrome(_list_to_nodes([1])) is True
    print("全部测试通过")
