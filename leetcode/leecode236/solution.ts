/**
 * 考点：树、DFS、二叉树
 * 题目：Lowest Common Ancestor of a Binary Tree（二叉树的最近公共祖先）
 * 题目描述：找到二叉树中两个节点的最近公共祖先。root=[3,5,1,6,2,0,8,null,null,7,4],p=5,q=1 输出 3
 * 思路：后序遍历，在左右子树找 p/q。若左右都有，则当前是 LCA；否则返回有值的那一侧。
 * 时间复杂度：O(n)
 * 空间复杂度：O(h)，h 为树高
 */

class TreeNode236 {
    val: number;
    left: TreeNode236 | null;
    right: TreeNode236 | null;
    constructor(val?: number, left?: TreeNode236 | null, right?: TreeNode236 | null) {
        this.val = val === undefined ? 0 : val;
        this.left = left === undefined ? null : left;
        this.right = right === undefined ? null : right;
    }
}

function lowestCommonAncestor(
    root: TreeNode236 | null,
    p: TreeNode236 | null,
    q: TreeNode236 | null
): TreeNode236 | null {
    if (root === null || root === p || root === q) return root;

    const left = lowestCommonAncestor(root.left, p, q);
    const right = lowestCommonAncestor(root.right, p, q);

    if (left !== null && right !== null) return root;
    return left !== null ? left : right;
}
export { lowestCommonAncestor, TreeNode236 };
