/**
 * 考点：Tree, DFS, BFS, Binary Tree
 * 题目：Path Sum（路径总和）
 * 题目描述：给定一个二叉树和一个目标和，判断该树中是否存在根节点到叶子节点的路径，这条路径上所有节点值相加等于目标和。
 * 叶子节点是指没有子节点的节点。
 * 示例 1：root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22，输出 true
 * 示例 2：root = [1,2,3], targetSum = 5，输出 false
 * 示例 3：root = [], targetSum = 0，输出 false
 * 思路：DFS 递归，每次减去当前节点值，到达叶子节点时检查剩余值是否为 0。
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

function hasPathSum(root: TreeNode | null, targetSum: number): boolean {
    if (root === null) return false;
    const remaining = targetSum - root.val;
    if (root.left === null && root.right === null) {
        return remaining === 0;
    }
    return hasPathSum(root.left, remaining) || hasPathSum(root.right, remaining);
}

export { hasPathSum, TreeNode };
