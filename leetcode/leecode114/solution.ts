/**
 * 考点：Stack, Tree, DFS, Linked List, Binary Tree
 * 题目：Flatten Binary Tree to Linked List（二叉树展开为链表）
 * 题目描述：将二叉树原地展开为一个单链表，展开后的单链表应该与二叉树先序遍历顺序相同，右指针指向链表下一个节点，左指针始终为 null。
 * 示例 1：root = [1,2,5,3,4,null,6]，输出 [1,null,2,null,3,null,4,null,5,null,6]
 * 示例 2：root = []，输出 []
 * 示例 3：root = [0]，输出 [0]
 * 思路：逆先序遍历（右-左-根），维护 prev 指针，将当前节点右指针指向 prev，左指针置 null。
 * 时间复杂度：O(n)
 * 空间复杂度：O(h)
 */
class TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
    constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
        this.val = val === undefined ? 0 : val;
        this.left = left === undefined ? null : left;
        this.right = right === undefined ? null : right;
    }
}

function flatten(root: TreeNode | null): void {
    let prev: TreeNode | null = null;

    function dfs(node: TreeNode | null): void {
        if (node === null) return;
        dfs(node.right);
        dfs(node.left);
        node.right = prev;
        node.left = null;
        prev = node;
    }

    dfs(root);
}

export { flatten, TreeNode };
