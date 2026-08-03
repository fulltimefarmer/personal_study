/**
 * 考点：Tree, DFS, BFS, Binary Tree
 * 题目：Symmetric Tree（对称二叉树）
 * 题目描述：给定二叉树根节点，检查是否轴对称。
 * 示例：root = [1,2,2,3,4,4,3] → true
 * 示例：root = [1,2,2,null,3,null,3] → false
 * 思路：DFS 递归。将问题转化为比较左右子树是否互为镜像。
 *       镜像条件：值相等，且 left.left 与 right.right 镜像，left.right 与 right.left 镜像。
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

function isSymmetric(root: TreeNode | null): boolean {
    if (!root) return true;

    function isMirror(left: TreeNode | null, right: TreeNode | null): boolean {
        if (!left && !right) return true;
        if (!left || !right) return false;
        if (left.val !== right.val) return false;
        return isMirror(left.left, right.right) && isMirror(left.right, right.left);
    }

    return isMirror(root.left, root.right);
}

export { isSymmetric, TreeNode };
