/**
 * 考点：Linked List, Recursion
 * 题目：Merge Two Sorted Lists（合并两个有序链表）
 * 题目描述：合并两个升序链表。如 [1,2,4] + [1,3,4] → [1,1,2,3,4,4]
 * 思路：递归，比较两个链表头节点，较小者作为当前节点，递归合并剩余部分。
 * 时间复杂度：O(m + n)
 * 空间复杂度：O(m + n)（递归栈）
 */

class ListNode {
    val: number;
    next: ListNode | null;
    constructor(val?: number, next?: ListNode | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function mergeTwoLists(l1: ListNode | null, l2: ListNode | null): ListNode | null {
    if (l1 === null) return l2;
    if (l2 === null) return l1;

    if (l1.val <= l2.val) {
        l1.next = mergeTwoLists(l1.next, l2);
        return l1;
    } else {
        l2.next = mergeTwoLists(l1, l2.next);
        return l2;
    }
}

export { mergeTwoLists, ListNode };
