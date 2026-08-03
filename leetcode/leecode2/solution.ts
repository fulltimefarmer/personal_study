/**
 * 考点：Linked List, Math
 * 题目：Add Two Numbers（两数相加）
 * 题目描述：给你两个非空的链表表示两个非负整数，每位数字按逆序存储，每个节点只存储一位数字。将两数相加并返回表示和的链表。
 * 示例：l1 = [2,4,3], l2 = [5,6,4] => [7,0,8]（342 + 465 = 807）
 * 思路：模拟加法过程，逐位相加并维护进位
 * 时间复杂度：O(max(m, n))
 * 空间复杂度：O(1)
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

    while (l1 !== null || l2 !== null || carry !== 0) {
        const val1 = l1 ? l1.val : 0;
        const val2 = l2 ? l2.val : 0;
        const sum = val1 + val2 + carry;

        carry = Math.floor(sum / 10);
        curr.next = new ListNode(sum % 10);
        curr = curr.next;

        if (l1) l1 = l1.next;
        if (l2) l2 = l2.next;
    }

    return dummy.next;
}
export { addTwoNumbers, ListNode };
