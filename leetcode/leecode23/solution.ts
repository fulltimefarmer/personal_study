/**
 * 考点：Linked List, Divide and Conquer, Heap
 * 题目：Merge k Sorted Lists（合并 K 个升序链表）
 * 题目描述：合并 k 个升序链表为一个升序链表。
 * 示例：lists = [[1,4,5],[1,3,4],[2,6]] => [1,1,2,3,4,4,5,6]
 * 思路：分治法，递归地将链表数组两两合并
 * 时间复杂度：O(N log k)
 * 空间复杂度：O(log k)
 */

class ListNode {
    val: number;
    next: ListNode | null;
    constructor(val?: number, next?: ListNode | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function mergeKLists(lists: Array<ListNode | null>): ListNode | null {
    if (lists.length === 0) return null;
    return mergeRange(lists, 0, lists.length - 1);
}

function mergeRange(lists: Array<ListNode | null>, left: number, right: number): ListNode | null {
    if (left === right) return lists[left];

    const mid = Math.floor((left + right) / 2);
    const l1 = mergeRange(lists, left, mid);
    const l2 = mergeRange(lists, mid + 1, right);

    return mergeTwoLists(l1, l2);
}

function mergeTwoLists(l1: ListNode | null, l2: ListNode | null): ListNode | null {
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

export { mergeKLists, ListNode };
