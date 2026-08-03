/**
 * 考点：树, DFS, 二叉树
 * 题目：Diameter of Binary Tree（二叉树的直径）
 * 题目描述：给定一棵二叉树，求直径（任意两节点间最长路径的边数）。
 * 示例：
 *   输入: root=[1,2,3,4,5] → 输出: 3 (路径[4,2,1,3])
 * 思路：DFS 后序遍历。递归计算每个节点的左右子树深度，经过当前节点的路径长为 left+right，全局更新最大值。
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

function diameterOfBinaryTree(root: TreeNode | null): number {
    let diameter = 0;

    function depth(node: TreeNode | null): number {
        if (node === null) return 0;

        const left = depth(node.left);
        const right = depth(node.right);

        diameter = Math.max(diameter, left + right);

        return Math.max(left, right) + 1;
    }

    depth(root);
    return diameter;
}

export { TreeNode, diameterOfBinaryTree };
