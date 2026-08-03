/**
 * 考点：Linked List
 * 题目：Reverse Linked List II（反转链表 II）
 * 题目描述：反转链表从 left 到 right 位置的节点（1-indexed）。
 * 示例：head = [1,2,3,4,5], left = 2, right = 4 → [1,4,3,2,5]
 * 思路：哑节点 + 头插法。找到 left 前驱 prev，对区间内每个节点，
 *       将其从链表中断开并头插到 prev 后面。
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

function reverseBetween(head: ListNode | null, left: number, right: number): ListNode | null {
    if (!head) return null;

    const dummy = new ListNode(0, head);
    let prev = dummy;

    for (let i = 0; i < left - 1; i++) {
        prev = prev.next!;
    }

    const curr = prev.next!;

    for (let i = 0; i < right - left; i++) {
        const next = curr.next!;
        curr.next = next.next;
        next.next = prev.next;
        prev.next = next;
    }

    return dummy.next;
}

export { reverseBetween, ListNode };
