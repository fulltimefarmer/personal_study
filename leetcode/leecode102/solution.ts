/**
 * 考点：Tree, BFS, Binary Tree
 * 题目：Binary Tree Level Order Traversal（二叉树的层序遍历）
 * 题目描述：给定二叉树根节点，返回层序遍历结果（按层分组，从左到右）。
 * 示例：root = [3,9,20,null,null,15,7] → [[3],[9,20],[15,7]]
 * 思路：BFS 队列。记录每层节点数 levelSize，依次处理该层所有节点，子节点入队。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
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

function levelOrder(root: TreeNode | null): number[][] {
    if (!root) return [];

    const result: number[][] = [];
    const queue: TreeNode[] = [root];

    while (queue.length > 0) {
        const levelSize = queue.length;
        const level: number[] = [];

        for (let i = 0; i < levelSize; i++) {
            const node = queue.shift()!;
            level.push(node.val);
            if (node.left) queue.push(node.left);
            if (node.right) queue.push(node.right);
        }

        result.push(level);
    }

    return result;
}

export { levelOrder, TreeNode };
