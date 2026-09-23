# Reverse Linked List — 考点分析与解题思路

## 考点分析

1. **链表指针操作**：反转链表是链表题的基本功，考查能否在不丢失节点的情况下安全地改动 `next` 指针。核心是「先保存后断链」的顺序。
2. **迭代三指针**：`prev`（已反转部分头）、`curr`（当前待反转）、`next`（暂存下一个节点）。每一步把 `curr.next` 指回 `prev`，再整体前移。
3. **递归思路**：把「反转整条链」分解为「反转除头以外的链 + 把头接到新链尾」。递归版更简洁，但要注意栈空间 O(n)。
4. **边界**：空链表、单节点链表、首尾指针为 `null` 的处理。

## 解题思路

### 方案 A：迭代（三指针）

- 初始化 `prev = null`，`curr = head`。
- 循环直到 `curr === null`：
  - `next = curr.next` 先保存后继（否则断链后丢失）；
  - `curr.next = prev` 反转指针；
  - `prev = curr`、`curr = next` 前移。
- 返回 `prev`（此时为原链表尾，即新链表头）。

### 方案 B：递归

- 递归基：`head === null || head.next === null` 返回 `head`。
- 递归反转 `head.next` 得到新头 `newHead`。
- 此时 `head.next` 已成为新链表的尾节点，令 `head.next.next = head`、`head.next = null`。
- 返回 `newHead`。

## 复杂度

- 时间：O(n)，遍历一次。
- 空间：迭代 O(1)；递归 O(n)（调用栈）。

## 参考代码（迭代）

```ts
function reverseList(head: ListNode | null): ListNode | null {
  let prev: ListNode | null = null;
  let curr: ListNode | null = head;
  while (curr) {
    const next: ListNode | null = curr.next; // 先保存后继
    curr.next = prev;                        // 反转指向
    prev = curr;                             // prev 前移
    curr = next;                             // curr 前移
  }
  return prev;
}
```

## 参考代码（递归）

```ts
function reverseList(head: ListNode | null): ListNode | null {
  if (!head || !head.next) return head;
  const newHead = reverseList(head.next);
  head.next.next = head;
  head.next = null;
  return newHead;
}
```

## 追问 / Follow-ups

1. **反转前 k 个节点** 或 **反转区间 `[left, right]`**（LeetCode 92）？→ 定位区间前驱，套用反转子链，再重新接上首尾。
2. **每 k 个一组翻转**（LeetCode 25）？→ 分段 + 反转 + 递归拼接。
3. **判断回文链表**（LeetCode 234）？→ 快慢指针找中点，反转后半段，再逐个比较。
