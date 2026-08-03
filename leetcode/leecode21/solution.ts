/**
 * 考点：Linked List, Recursion
 * 题目：Merge Two Sorted Lists（合并两个有序链表）
 * 题目描述：将两个升序链表合并为一个新的升序链表并返回。
 * 示例：l1 = [1,2,4], l2 = [1,3,4] => [1,1,2,3,4,4]
 * 思路：迭代法，比较两链表当前节点，将较小的接入结果链表
 * 时间复杂度：O(m + n)
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

function mergeTwoLists(list1: ListNode | null, list2: ListNode | null): ListNode | null {
    const dummy = new ListNode(0);
    let curr = dummy;

    while (list1 !== null && list2 !== null) {
        if (list1.val <= list2.val) {
            curr.next = list1;
            list1 = list1.next;
        } else {
            curr.next = list2;
            list2 = list2.next;
        }
        curr = curr.next;
    }

    curr.next = list1 !== null ? list1 : list2;

    return dummy.next;
}
export { mergeTwoLists, ListNode };
