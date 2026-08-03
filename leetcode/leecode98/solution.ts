/**
 * 考点：Tree, DFS, BST, Binary Tree
 * 题目：Validate Binary Search Tree（验证二叉搜索树）
 * 题目描述：给定二叉树根节点，判断是否是有效的 BST。
 *       左子树所有节点小于根，右子树所有节点大于根，且左右子树也是 BST。
 * 示例：root = [2,1,3] → true
 * 示例：root = [5,1,4,null,null,3,6] → false
 * 思路：递归带上下界。每个节点的值必须在 (lower, upper) 范围内。
 *       左子树更新上界为 root.val，右子树更新下界为 root.val。
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

function isValidBST(root: TreeNode | null): boolean {
    function validate(node: TreeNode | null, lower: number, upper: number): boolean {
        if (!node) return true;
        if (node.val <= lower || node.val >= upper) return false;
        return validate(node.left, lower, node.val) && validate(node.right, node.val, upper);
    }

    return validate(root, -Infinity, Infinity);
}

export { isValidBST, TreeNode };
