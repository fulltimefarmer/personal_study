/**
 * 考点：Tree, DFS, BFS, Binary Tree
 * 题目：Same Tree（相同的树）
 * 题目描述：给定两棵二叉树的根节点 p 和 q，判断两棵树是否完全相同（结构和值）。
 * 示例：p = [1,2,3], q = [1,2,3] → true
 * 示例：p = [1,2], q = [1,null,2] → false
 * 思路：DFS 递归。同时遍历两棵树，比较对应节点的值。
 *       都为空返回 true，只有一个为空或值不等返回 false，递归比较左右子树。
 * 时间复杂度：O(min(n1, n2))
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

function isSameTree(p: TreeNode | null, q: TreeNode | null): boolean {
    if (!p && !q) return true;
    if (!p || !q) return false;
    if (p.val !== q.val) return false;
    return isSameTree(p.left, q.left) && isSameTree(p.right, q.right);
}

export { isSameTree, TreeNode };
