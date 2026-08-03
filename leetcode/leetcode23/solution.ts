/**
 * 考点：Linked List, Divide and Conquer, Heap
 * 题目：Merge k Sorted Lists（合并K个升序链表）
 * 题目描述：合并k个升序链表。如 [[1,4,5],[1,3,4],[2,6]] → [1,1,2,3,4,4,5,6]
 * 思路：分治法，两两合并，类似归并排序。mergeTwoLists 复用 #21 的逻辑。
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

function mergeTwo(a: ListNode | null, b: ListNode | null): ListNode | null {
    if (!a) return b;
    if (!b) return a;
    if (a.val <= b.val) {
        a.next = mergeTwo(a.next, b);
        return a;
    }
    b.next = mergeTwo(a, b.next);
    return b;
}

function mergeKLists(lists: Array<ListNode | null>): ListNode | null {
    if (lists.length === 0) return null;

    function divide(left: number, right: number): ListNode | null {
        if (left === right) return lists[left];
        if (left > right) return null;
        const mid = (left + right) >> 1;
        return mergeTwo(divide(left, mid), divide(mid + 1, right));
    }

    return divide(0, lists.length - 1);
}

export { mergeKLists, ListNode };
