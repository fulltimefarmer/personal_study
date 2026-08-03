"""
考点：链表、数学
题目：Add Two Numbers（两数相加）
思路：模拟加法竖式，使用哑节点简化链表构建，逐位相加并维护进位 carry
时间复杂度：O(max(m, n))
空间复杂度：O(1)（不计返回结果）
"""
from typing import Optional

class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None):
        self.val = val
        self.next = next

def addTwoNumbers(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    # 哑节点：简化链表操作，避免处理空链表边界情况
    # 它的 next 指向真正的结果链表头节点
    dummy = ListNode(0)
    curr = dummy
    carry = 0  # 进位值，范围 0 或 1

    # 只要还有未处理的节点或者有进位，就继续循环
    while l1 is not None or l2 is not None or carry != 0:
        # 使用 Python 3.8+ 的海象运算符 := 在表达式中赋值
        # type: ignore 用于告诉类型检查器忽略此处的可选类型检查
        val1 = l1.val if l1 else 0  # 三元表达式：若 l1 非空取 val，否则取 0
        val2 = l2.val if l2 else 0
        total = val1 + val2 + carry  # 当前位的总和

        carry = total // 10  # 整除：计算新的进位（Python 中 // 是地板除）
        curr.next = ListNode(total % 10)  # 取模：当前位只保留个位数字
        curr = curr.next

        if l1:
            l1 = l1.next  # 移动 l1 指针到下一个节点
        if l2:
            l2 = l2.next  # 移动 l2 指针到下一个节点

    return dummy.next  # 返回哑节点的下一个，即真正的结果链表头

if __name__ == "__main__":
    # 构建链表辅助函数
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

    # 示例：342 + 465 = 807
    l1 = build_list([2, 4, 3])
    l2 = build_list([5, 6, 4])
    assert list_to_array(addTwoNumbers(l1, l2)) == [7, 0, 8]

    # 示例：0 + 0 = 0
    assert list_to_array(addTwoNumbers(build_list([0]), build_list([0]))) == [0]

    # 示例：9999999 + 9999
    l1 = build_list([9, 9, 9, 9, 9, 9, 9])
    l2 = build_list([9, 9, 9, 9])
    assert list_to_array(addTwoNumbers(l1, l2)) == [8, 9, 9, 9, 0, 0, 0, 1]
    print("全部通过 ✓")
