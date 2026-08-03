/**
 * 考点：Hash Table, Linked List, Two Pointers
 * 题目：Linked List Cycle II（环形链表II）
 * 题目描述：返回链表环的入口节点，无环返回 null。不允许修改链表。
 * 示例 1：head=[3,2,0,-4], pos=1，返回索引为 1 的节点
 * 示例 2：head=[1,2], pos=0，返回索引为 0 的节点
 * 示例 3：head=[1], pos=-1，返回 null
 * 思路：快慢指针检测环 → 相遇后慢指针回头部，同步移动再次相遇即为入口。
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

function detectCycle(head: ListNode | null): ListNode | null {
    let slow: ListNode | null = head;
    let fast: ListNode | null = head;

    while (fast !== null && fast.next !== null) {
        slow = slow!.next;
        fast = fast.next.next;
        if (slow === fast) {
            slow = head;
            while (slow !== fast) {
                slow = slow!.next;
                fast = fast!.next;
            }
            return slow;
        }
    }

    return null;
}

export { detectCycle, ListNode };
