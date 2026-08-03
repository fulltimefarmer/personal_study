/**
 * 考点：哈希表、链表、双指针
 * 题目：Intersection of Two Linked Lists（相交链表）
 * 题目描述：找到两个单链表相交的起始节点。不相交则返回 null。
 *   示例：listA = [4,1,8,4,5], listB = [5,6,1,8,4,5] → 相交于节点 8
 * 思路：双指针。pA 从 A 走到头后转到 B，pB 从 B 走到头后转到 A。
 *   两者走过的总路程相同 (a+b+c)，若相交则会在交点相遇，不相交则同时为 null。
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

function getIntersectionNode(
  headA: ListNode | null,
  headB: ListNode | null
): ListNode | null {
  let pA = headA;
  let pB = headB;

  while (pA !== pB) {
    pA = pA === null ? headB : pA.next;
    pB = pB === null ? headA : pB.next;
  }

  return pA;
}

export { getIntersectionNode, ListNode };
