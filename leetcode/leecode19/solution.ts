/**
 * 考点：Linked List, Two Pointers
 * 题目：Remove Nth Node From End of List（删除链表的倒数第 N 个结点）
 * 题目描述：删除链表的倒数第 n 个结点，并返回头结点。
 * 示例：head = [1,2,3,4,5], n = 2 => [1,2,3,5]
 * 思路：快慢指针，快指针先走 n+1 步，然后一起移动，慢指针到达删除位置的前驱节点
 * 时间复杂度：O(L)
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

function removeNthFromEnd(head: ListNode | null, n: number): ListNode | null {
    const dummy = new ListNode(0, head);
    let fast: ListNode | null = dummy;
    let slow: ListNode | null = dummy;

    for (let i = 0; i <= n; i++) {
        fast = fast!.next;
    }

    while (fast !== null) {
        fast = fast.next;
        slow = slow!.next;
    }

    slow!.next = slow!.next!.next;

    return dummy.next;
}
export { removeNthFromEnd, ListNode };
