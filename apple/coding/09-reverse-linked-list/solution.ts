// Reverse Linked List — 代码空壳（CoderPad 中填充）
// 反转单链表并返回新头节点。

class ListNode {
  val: number;
  next: ListNode | null;
  constructor(val?: number, next?: ListNode | null) {
    this.val = val === undefined ? 0 : val;
    this.next = next === undefined ? null : next;
  }
}

function reverseList(head: ListNode | null): ListNode | null {
  // TODO: 迭代三指针 prev/curr/next，或递归反转
  return null;
}

// —— 测试（可运行验证）——
function build(values: number[]): ListNode | null {
  let head: ListNode | null = null;
  for (let i = values.length - 1; i >= 0; i--) {
    head = new ListNode(values[i], head);
  }
  return head;
}

function toArray(head: ListNode | null): number[] {
  const res: number[] = [];
  while (head) {
    res.push(head.val);
    head = head.next;
  }
  return res;
}

function run() {
  console.log(JSON.stringify(toArray(reverseList(build([1, 2, 3, 4, 5]))))); // [5,4,3,2,1]
  console.log(JSON.stringify(toArray(reverseList(build([1, 2])))));         // [2,1]
  console.log(JSON.stringify(toArray(reverseList(build([])))));             // []
}

run();
