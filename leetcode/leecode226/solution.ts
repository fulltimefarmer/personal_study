/**
 * 考点：树、DFS、BFS、二叉树
 * 题目：Invert Binary Tree（翻转二叉树）
 * 题目描述：翻转二叉树，交换每个节点的左右子树。root=[4,2,7,1,3,6,9] 输出 [4,7,2,9,6,3,1]
 * 思路：递归，翻转左右子树后交换当前节点的左右孩子。
 * 时间复杂度：O(n)
 * 空间复杂度：O(h)，h 为树高（递归栈），最坏 O(n)
 */

class TreeNode226 {
    val: number;
    left: TreeNode226 | null;
    right: TreeNode226 | null;
    constructor(val?: number, left?: TreeNode226 | null, right?: TreeNode226 | null) {
        this.val = val === undefined ? 0 : val;
        this.left = left === undefined ? null : left;
        this.right = right === undefined ? null : right;
    }
}

function invertTree(root: TreeNode226 | null): TreeNode226 | null {
    if (root === null) return null;

    const left = invertTree(root.left);
    const right = invertTree(root.right);
    root.left = right;
    root.right = left;

    return root;
}
export { invertTree, TreeNode226 };
