/**
 * 考点：Linked List, Two Pointers, Divide and Conquer, Sorting, Merge Sort
 * 题目：Sort List（排序链表）
 * 题目描述：对链表进行升序排序，O(n log n) 时间，O(1) 空间（进阶）。
 * 示例 1：[4,2,1,3]，输出 [1,2,3,4]
 * 示例 2：[-1,5,3,4,0]，输出 [-1,0,3,4,5]
 * 示例 3：[]，输出 []
 * 思路：归并排序。快慢指针找中点，递归排序左右，合并有序链表。
 * 时间复杂度：O(n log n)
 * 空间复杂度：O(log n)
 */
class ListNode {
    val: number;
    next: ListNode | null;
    constructor(val?: number, next?: ListNode | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function sortList(head: ListNode | null): ListNode | null {
    if (head === null || head.next === null) return head;

    let slow: ListNode | null = head;
    let fast: ListNode | null = head.next;

    while (fast !== null && fast.next !== null) {
        slow = slow!.next;
        fast = fast.next.next;
    }

    const mid = slow!.next;
    slow!.next = null;

    const left = sortList(head);
    const right = sortList(mid);

    return merge(left, right);
}

function merge(l1: ListNode | null, l2: ListNode | null): ListNode | null {
    const dummy = new ListNode(0);
    let curr = dummy;

    while (l1 !== null && l2 !== null) {
        if (l1.val <= l2.val) {
            curr.next = l1;
            l1 = l1.next;
        } else {
            curr.next = l2;
            l2 = l2.next;
        }
        curr = curr.next;
    }

    curr.next = l1 !== null ? l1 : l2;
    return dummy.next;
}

export { sortList, ListNode };
