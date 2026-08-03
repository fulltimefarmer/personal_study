/**
 * 考点：Linked List, Math
 * 题目：Add Two Numbers（两数相加）
 * 题目描述：两个逆序存储的非负整数链表，逐位相加返回和链表。342 + 465 = 807，即 [2,4,3] + [5,6,4] = [7,0,8]
 * 思路：同时遍历两个链表，逐位相加处理进位。短链表结束后补0。注意最后的进位。
 * 时间复杂度：O(max(m, n))
 * 空间复杂度：O(max(m, n))
 */

class ListNode {
    val: number;
    next: ListNode | null;
    constructor(val?: number, next?: ListNode | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function addTwoNumbers(l1: ListNode | null, l2: ListNode | null): ListNode | null {
    const dummy = new ListNode(0);
    let curr = dummy;
    let carry = 0;

    while (l1 !== null || l2 !== null) {
        const val1 = l1 ? l1.val : 0;
        const val2 = l2 ? l2.val : 0;
        const sum = val1 + val2 + carry;

        carry = Math.floor(sum / 10);
        curr.next = new ListNode(sum % 10);
        curr = curr.next;

        if (l1) l1 = l1.next;
        if (l2) l2 = l2.next;
    }

    if (carry > 0) {
        curr.next = new ListNode(carry);
    }

    return dummy.next;
}

export { addTwoNumbers, ListNode };
