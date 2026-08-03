/**
 * 考点：链表、双指针、分治、排序、归并排序
 * 题目：Sort List（排序链表）
 * 题目描述：对链表进行升序排序，要求 O(n log n) 时间复杂度。
 *   示例：head = [4,2,1,3] → [1,2,3,4]
 * 思路：自底向上归并排序，O(1) 空间。按 sublen 逐步增大区间合并。
 * 时间复杂度：O(n log n)
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

function sortList(head: ListNode | null): ListNode | null {
  if (head === null || head.next === null) {
    return head;
  }

  let n = 0;
  let curr: ListNode | null = head;
  while (curr !== null) {
    n++;
    curr = curr.next;
  }

  const dummy = new ListNode(0, head);

  for (let subLen = 1; subLen < n; subLen *= 2) {
    let prev = dummy;
    let curr: ListNode | null = dummy.next;

    while (curr !== null) {
      const head1 = curr;
      for (let i = 1; i < subLen && curr.next !== null; i++) {
        curr = curr.next;
      }
      const head2 = curr.next;
      curr.next = null;
      curr = head2;
      if (curr !== null) {
        for (let i = 1; i < subLen && curr.next !== null; i++) {
          curr = curr.next;
        }
        const next = curr.next;
        curr.next = null;
        curr = next;
      }
      prev.next = merge(head1, head2);
      while (prev.next !== null) {
        prev = prev.next;
      }
      prev.next = curr;
    }
  }

  return dummy.next;
}

function merge(l1: ListNode | null, l2: ListNode | null): ListNode | null {
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

export { sortList, ListNode };
