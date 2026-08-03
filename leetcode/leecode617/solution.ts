/**
 * 考点：树, DFS, BFS, 二叉树
 * 题目：Merge Two Binary Trees（合并二叉树）
 * 题目描述：合并两棵二叉树，重叠节点值相加，不重叠的节点保留不为空的。返回合并后的二叉树。
 * 示例：
 *   输入: root1=[1,3,2,5], root2=[2,1,3,null,4,null,7] → 输出: [3,4,5,5,4,null,7]
 * 思路：DFS 递归。若任一节点为 null 则返回另一个节点。否则值相加，递归合并左右子树。
 * 时间复杂度：O(min(n1, n2))
 * 空间复杂度：O(min(h1, h2))
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

function mergeTrees(root1: TreeNode | null, root2: TreeNode | null): TreeNode | null {
    if (root1 === null) return root2;
    if (root2 === null) return root1;

    root1.val += root2.val;
    root1.left = mergeTrees(root1.left, root2.left);
    root1.right = mergeTrees(root1.right, root2.right);

    return root1;
}

export { TreeNode, mergeTrees };
