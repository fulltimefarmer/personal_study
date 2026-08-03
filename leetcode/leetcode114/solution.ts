/**
 * 考点：栈、树、DFS、链表、二叉树
 * 题目：Flatten Binary Tree to Linked List（二叉树展开为链表）
 * 题目描述：将二叉树按先序遍历展开为单链表，使用 right 指针作为 next，left 指针置为 null。
 *   示例：root = [1,2,5,3,4,null,6] → [1,null,2,null,3,null,4,null,5,null,6]
 * 思路：反向前序遍历（右-左-根）。用 prev 记录上一个处理的节点，
 *   按右→左→根顺序遍历，将当前节点 right 指向 prev，left 置为 null。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)，递归栈
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

/**
 * Do not return anything, modify root in-place instead.
 */
function flatten(root: TreeNode | null): void {
  let prev: TreeNode | null = null;

  function dfs(node: TreeNode | null): void {
    if (node === null) {
      return;
    }
    dfs(node.right);
    dfs(node.left);
    node.right = prev;
    node.left = null;
    prev = node;
  }

  dfs(root);
}

export { flatten, TreeNode };
