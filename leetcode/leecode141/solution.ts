/**
 * 考点：Hash Table, Linked List, Two Pointers
 * 题目：Linked List Cycle（环形链表）
 * 题目描述：判断链表是否有环。
 * 示例 1：head=[3,2,0,-4], pos=1，输出 true
 * 示例 2：head=[1,2], pos=0，输出 true
 * 示例 3：head=[1], pos=-1，输出 false
 * 思路：快慢指针，快指针每次两步，慢指针一步。有环则相遇，无环则快指针先到 null。
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

function hasCycle(head: ListNode | null): boolean {
    let slow: ListNode | null = head;
    let fast: ListNode | null = head;

    while (fast !== null && fast.next !== null) {
        slow = slow!.next;
        fast = fast.next.next;
        if (slow === fast) return true;
    }

    return false;
}

export { hasCycle, ListNode };
