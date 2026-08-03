/**
 * 考点：栈、递归、链表、双指针
 * 题目：Palindrome Linked List（回文链表）
 * 题目描述：判断单链表是否为回文。head=[1,2,2,1] 输出 true
 * 思路：快慢指针找中点，反转后半部分，前后比较。O(n) 时间 O(1) 空间。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

class ListNode234 {
    val: number;
    next: ListNode234 | null;
    constructor(val?: number, next?: ListNode234 | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function isPalindrome(head: ListNode234 | null): boolean {
    if (head === null || head.next === null) return true;

    let slow: ListNode234 | null = head;
    let fast: ListNode234 | null = head;

    while (fast !== null && fast.next !== null) {
        slow = slow!.next;
        fast = fast.next.next;
    }

    let prev: ListNode234 | null = null;
    while (slow !== null) {
        const next: ListNode234 | null = slow.next;
        slow.next = prev;
        prev = slow;
        slow = next;
    }

    let left: ListNode234 | null = head;
    let right: ListNode234 | null = prev;

    while (right !== null) {
        if (left!.val !== right.val) return false;
        left = left!.next;
        right = right.next;
    }

    return true;
}
export { isPalindrome, ListNode234 };
