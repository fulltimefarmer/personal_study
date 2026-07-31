/**
 * 考点：Linked List
 * 题目：Reverse Linked List
 * 题目描述：
 * 给你单链表的头节点 head，请你反转链表，并返回反转后的链表的头节点。
 *
 * 示例 1：
 * 输入：head = [1,2,3,4,5]
 * 输出：[5,4,3,2,1]
 *
 * 示例 2：
 * 输入：head = [1,2]
 * 输出：[2,1]
 *
 * 示例 3：
 * 输入：head = []
 * 输出：[]
 *
 * 提示：
 * - 链表中节点的数目范围是 [0, 5000]
 * - -5000 <= Node.val <= 5000
 *
 * 进阶：链表可以选用迭代或递归方式翻转。能否用两种方法解决？
 *
 * 思路：
 * 1. 使用迭代法，初始化 prev 为 null，cur 为 head。
 * 2. 遍历链表，每次先保存当前节点的下一个节点 next = cur.next。
 * 3. 将当前节点的 next 指针指向 prev，完成当前节点的反转。
 * 4. 更新 prev 为当前节点 cur，cur 为 next，继续处理下一个节点。
 * 5. 当 cur 为 null 时，prev 即为反转后的新头节点，返回 prev。
 * 数据结构/算法：单链表；迭代指针反转。
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

function reverseList(head: ListNode | null): ListNode | null {
    let prev: ListNode | null = null;
    let cur: ListNode | null = head;
    while (cur) {
        const next = cur.next;
        cur.next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}
