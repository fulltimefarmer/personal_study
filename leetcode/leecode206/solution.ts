/**
 * 考点：递归、链表
 * 题目：Reverse Linked List（反转链表）
 * 题目描述：反转单链表。head=[1,2,3,4,5] 输出 [5,4,3,2,1]
 * 思路：迭代法，pre/cur/next 三指针，cur.next=pre 逐个反转。
 * 时间复杂度：O(n)
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

function reverseList(head: ListNode | null): ListNode | null {
    let prev: ListNode | null = null;
    let cur: ListNode | null = head;

    while (cur !== null) {
        const next: ListNode | null = cur.next;
        cur.next = prev;
        prev = cur;
        cur = next;
    }

    return prev;
}
export { reverseList, ListNode };
