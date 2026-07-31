/**
 * 考点：Linked List、Recursion
 * 题目：Merge Two Sorted Lists
 * 题目描述：
 *   将两个升序链表合并为一个新的升序链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。
 *   示例 1：输入 list1 = [1,2,4], list2 = [1,3,4]，输出 [1,1,2,3,4,4]。
 *   示例 2：输入 list1 = [], list2 = []，输出 []。
 *   示例 3：输入 list1 = [], list2 = [0]，输出 [0]。
 *   提示：两个链表的节点数目范围是 [0, 50]，-100 <= Node.val <= 100，list1 和 list2 均按非递减顺序排列。
 * 思路：
 *   1. 递归函数 mergeTwoLists(list1, list2) 比较两个链表当前的头节点。
 *   2. 若其中一个链表为空，直接返回另一个链表，作为递归终止条件。
 *   3. 若 list1.val < list2.val，则 list1 作为当前合并链表的较小节点，让 list1.next 指向 mergeTwoLists(list1.next, list2) 的返回结果，并返回 list1。
 *   4. 否则，list2 作为当前较小节点，让 list2.next 指向 mergeTwoLists(list1, list2.next)，并返回 list2。
 *   5. 递归层层返回，最终得到一条完整有序的合并链表。
 * 数据结构：链表（Linked List）—— 节点按顺序连接，每个节点包含值和 next 指针。
 * 时间复杂度：O(n + m)
 * 空间复杂度：O(n + m)，递归栈空间
 */
class ListNode {
    val: number;
    next: ListNode | null;
    constructor(val?: number, next?: ListNode | null) {
        this.val = val === undefined ? 0 : val;
        this.next = next === undefined ? null : next;
    }
}

function mergeTwoLists(list1: ListNode | null, list2: ListNode | null): ListNode | null {
    if (list1 === null) return list2;
    if (list2 === null) return list1;
    if (list1.val < list2.val) {
        list1.next = mergeTwoLists(list1.next, list2);
        return list1;
    } else {
        list2.next = mergeTwoLists(list1, list2.next);
        return list2;
    }
}
