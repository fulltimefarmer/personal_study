/**
 * 考点：Tree, DFS, BFS, Binary Tree
 * 题目：Maximum Depth of Binary Tree（二叉树的最大深度）
 * 题目描述：给定二叉树，返回从根到最远叶子节点的最长路径上的节点数。
 * 示例：root = [3,9,20,null,null,15,7] → 3
 * 思路：DFS 递归。最大深度 = 1 + max(左子树深度, 右子树深度)。
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

function maxDepth(root: TreeNode | null): number {
    if (!root) return 0;
    return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}

export { maxDepth, TreeNode };
