/**
 * 考点：Hash Table, Linked List, Two Pointers
 * 题目：Intersection of Two Linked Lists（相交链表）
 * 题目描述：找两个链表的相交起始节点，不相交返回 null。链表无环。
 * 示例 1：listA=[4,1,8,4,5], listB=[5,6,1,8,4,5]，相交于节点 8
 * 示例 2：listA=[1,9,1,2,4], listB=[3,2,4]，相交于节点 2
 * 示例 3：listA=[2,6,4], listB=[1,5]，无相交
 * 思路：双指针，各走完整链表后切换到对方头部。有交点则相遇，无交点则同时到 null。
 * 路径：pA: a+c+b, pB: b+c+a，两者相等。
 * 时间复杂度：O(m+n)
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

function getIntersectionNode(headA: ListNode | null, headB: ListNode | null): ListNode | null {
    let pA: ListNode | null = headA;
    let pB: ListNode | null = headB;

    while (pA !== pB) {
        pA = pA === null ? headB : pA.next;
        pB = pB === null ? headA : pB.next;
    }

    return pA;
}

export { getIntersectionNode, ListNode };
