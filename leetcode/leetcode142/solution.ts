/**
 * 考点：哈希表、链表、双指针
 * 题目：Linked List Cycle II（环形链表 II）
 * 题目描述：返回链表入环的第一个节点。如果无环则返回 null。
 *   示例：head = [3,2,0,-4], pos = 1 → 返回值为 2 的节点
 * 思路：快慢指针。先用快慢指针找相遇点，然后将一个指针移到 head，同速前进相遇即入环点。
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
  let slow = head;
  let fast = head;

  while (fast !== null && fast.next !== null) {
    slow = slow!.next;
    fast = fast.next.next;
    if (slow === fast) {
      let ptr1 = head;
      let ptr2 = slow;
      while (ptr1 !== ptr2) {
        ptr1 = ptr1!.next;
        ptr2 = ptr2!.next;
      }
      return ptr1;
    }
  }

  return null;
}

export { detectCycle, ListNode };
