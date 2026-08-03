/**
 * 考点：哈希表、链表、双指针
 * 题目：Linked List Cycle（环形链表）
 * 题目描述：判断链表中是否有环。
 *   示例：head = [3,2,0,-4], pos = 1 → true
 * 思路：快慢指针。slow 每次一步，fast 每次两步。有环则必定相遇。
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
  let slow = head;
  let fast = head;

  while (fast !== null && fast.next !== null) {
    slow = slow!.next;
    fast = fast.next.next;
    if (slow === fast) {
      return true;
    }
  }

  return false;
}

export { hasCycle, ListNode };
