/**
 * 考点：哈希表、链表
 * 题目：Copy List with Random Pointer（随机链表的复制）
 * 题目描述：深拷贝一个带 random 指针的链表。新链表的 next 和 random 都指向新节点。
 *   示例：head = [[7,null],[13,0],[11,4],[10,2],[1,0]]
 * 思路：节点交错法，O(1) 额外空间。
 *   1. 每个原节点后插入副本：A→A'→B→B'
 *   2. 设置副本的 random：A'.random = A.random.next
 *   3. 拆分两个链表
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */

class Node {
  val: number;
  next: Node | null;
  random: Node | null;
  constructor(val?: number, next?: Node | null, random?: Node | null) {
    this.val = val === undefined ? 0 : val;
    this.next = next === undefined ? null : next;
    this.random = random === undefined ? null : random;
  }
}

function copyRandomList(head: Node | null): Node | null {
  if (head === null) {
    return null;
  }

  let curr: Node | null = head;
  while (curr !== null) {
    const copy = new Node(curr.val, curr.next, null);
    curr.next = copy;
    curr = copy.next;
  }

  curr = head;
  while (curr !== null) {
    if (curr.random !== null) {
      curr.next!.random = curr.random.next;
    }
    curr = curr.next!.next;
  }

  curr = head;
  const copyHead = head.next!;
  while (curr !== null) {
    const copy = curr.next!;
    curr.next = copy.next;
    if (copy.next !== null) {
      copy.next = copy.next.next;
    }
    curr = curr.next;
  }

  return copyHead;
}

export { copyRandomList, Node };
