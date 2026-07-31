/**
 * 考点：Linked List, Two Pointers, Floyd Cycle Detection
 * 题目：Linked List Cycle
 * 题目描述：
 * 给你一个链表的头节点 head，判断链表中是否有环。
 *
 * 如果链表中有某个节点，可以通过连续跟踪 next 指针再次到达，则链表中存在环。
 * 为了表示给定链表中的环，评测系统内部使用整数 pos 来表示链表尾连接到链表中的位置（索引从 0 开始）。注意：pos 不作为参数进行传递，仅仅是为了标识链表的实际情况。
 * 如果链表中存在环，则返回 true；否则，返回 false。
 *
 * 示例 1：
 * 输入：head = [3,2,0,-4], pos = 1
 * 输出：true
 * 解释：链表中有一个环，其尾部连接到第二个节点。
 *
 * 示例 2：
 * 输入：head = [1,2], pos = 0
 * 输出：true
 * 解释：链表中有一个环，其尾部连接到第一个节点。
 *
 * 示例 3：
 * 输入：head = [1], pos = -1
 * 输出：false
 * 解释：链表中没有环。
 *
 * 提示：
 * - 链表中节点的数目范围是 [0, 10^4]
 * - -10^5 <= Node.val <= 10^5
 * - pos 为 -1 或者链表中的一个有效索引
 *
 * 思路：
 * 1. 使用 Floyd 判圈算法（快慢指针），初始化 slow 和 fast 指针均指向 head。
 * 2. 慢指针 slow 每次前进一步，快指针 fast 每次前进两步。
 * 3. 如果链表中无环，fast 指针会先到达链表末尾（fast 为 null 或 fast.next 为 null）。
 * 4. 如果链表中有环，fast 指针会进入环并不断绕圈，最终追上 slow 指针，两者相遇。
 * 5. 若相遇则返回 true，否则返回 false。
 * 数据结构/算法：双指针；单链表节点 ListNode 含 val、next。
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 */
class ListNode {
    int val;
    ListNode next;

    ListNode(int x) {
        val = x;
        next = null;
    }
}

public class Solution {
    public boolean hasCycle(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false;
    }
}
