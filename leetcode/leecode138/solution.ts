/**
 * 考点：Hash Table, Linked List
 * 题目：Copy List with Random Pointer（随机链表的复制）
 * 题目描述：深拷贝带随机指针的链表。新节点值相同，next 和 random 指向复制链表中对应的新节点。
 * 示例：head = [[7,null],[13,0],[11,4],[10,2],[1,0]]，输出同样的结构。
 * 思路：HashMap 存储原节点→新节点的映射，两遍遍历建立 next 和 random 关系。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
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
    if (head === null) return null;

    const map = new Map<Node, Node>();

    let curr: Node | null = head;
    while (curr !== null) {
        map.set(curr, new Node(curr.val));
        curr = curr.next;
    }

    curr = head;
    while (curr !== null) {
        const copy = map.get(curr)!;
        copy.next = curr.next ? map.get(curr.next)! : null;
        copy.random = curr.random ? map.get(curr.random)! : null;
        curr = curr.next;
    }

    return map.get(head)!;
}

export { copyRandomList, Node };
