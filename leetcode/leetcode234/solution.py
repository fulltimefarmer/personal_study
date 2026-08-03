"""
考点：链表、双指针、递归
题目：Palindrome Linked List（回文链表）
题目描述：判断一个单链表是否是回文链表。
  示例：head = [1,2,2,1] → true；head = [1,2] → false
思路：快慢指针找中点 + 反转后半段链表 + 比较。
  1. 快慢指针找到链表中点
  2. 反转后半段链表
  3. 比较前半段和反转后的后半段
  4. （可选）恢复链表
时间复杂度：O(n)
空间复杂度：O(1)
"""


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next


def isPalindrome(head: ListNode | None) -> bool:
    if not head or not head.next:
        return True  # 空链表或只有一个节点，是回文

    # 步骤1：快慢指针找中点（slow 到达中点或下半部分起点）
    slow = head
    fast: ListNode | None = head
    while fast and fast.next:
        slow = slow.next  # type: ignore[assignment]  # slow 不可能为 None
        fast = fast.next.next

    # 步骤2：反转后半段链表（从 slow 开始）
    prev: ListNode | None = None
    curr: ListNode | None = slow
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    # prev 现在是反转后的后半段头节点

    # 步骤3：比较前半段和反转后的后半段
    left = head
    right = prev
    while right:  # 后半段长度 <= 前半段，用后半段长度判断
        if left.val != right.val:
            return False
        left = left.next
        right = right.next

    return True


def build_list(values: list[int]) -> ListNode | None:
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


if __name__ == "__main__":
    assert isPalindrome(build_list([1, 2, 2, 1])) is True
    assert isPalindrome(build_list([1, 2])) is False
    assert isPalindrome(build_list([1])) is True
