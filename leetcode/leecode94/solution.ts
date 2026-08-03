/**
 * 考点：Stack, Tree, DFS, Binary Tree
 * 题目：Binary Tree Inorder Traversal（二叉树的中序遍历）
 * 题目描述：给定二叉树根节点 root，返回中序遍历结果（左 → 根 → 右）。
 * 示例：root = [1,null,2,3] → [1,3,2]
 * 思路：迭代法。使用栈模拟递归，沿左链入栈，弹出访问后转向右子树。
 * 时间复杂度：O(n)
 * 空间复杂度：O(h)，h 为树高
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

function inorderTraversal(root: TreeNode | null): number[] {
    const result: number[] = [];
    const stack: TreeNode[] = [];
    let current = root;

    while (current || stack.length > 0) {
        while (current) {
            stack.push(current);
            current = current.left;
        }
        current = stack.pop()!;
        result.push(current.val);
        current = current.right;
    }

    return result;
}

export { inorderTraversal, TreeNode };
