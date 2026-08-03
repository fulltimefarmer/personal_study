/**
 * 考点：Tree, DFS, DP, Binary Tree
 * 题目：Binary Tree Maximum Path Sum（二叉树中的最大路径和）
 * 题目描述：求二叉树中最大路径和。路径起点和终点任意，至少包含一个节点，不一定经过根。
 * 示例 1：[1,2,3]，输出 6（2→1→3）
 * 示例 2：[-10,9,20,null,null,15,7]，输出 42（15→20→7）
 * 思路：DFS 后序遍历，计算每个节点的最大贡献，更新全局最大值。
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

function maxPathSum(root: TreeNode | null): number {
    let maxSum = -Infinity;

    function maxGain(node: TreeNode | null): number {
        if (node === null) return 0;
        const leftGain = Math.max(maxGain(node.left), 0);
        const rightGain = Math.max(maxGain(node.right), 0);
        const currentSum = node.val + leftGain + rightGain;
        maxSum = Math.max(maxSum, currentSum);
        return node.val + Math.max(leftGain, rightGain);
    }

    maxGain(root);
    return maxSum;
}

export { maxPathSum, TreeNode };
