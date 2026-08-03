/**
 * 考点：树、DFS、动态规划、二叉树
 * 题目：Binary Tree Maximum Path Sum（二叉树中的最大路径和）
 * 题目描述：求二叉树中任意路径的最大路径和。路径至少包含一个节点，不一定经过根节点。
 *   示例：root = [-10,9,20,null,null,15,7] → 42（15→20→7）
 * 思路：DFS 递归。每个节点返回向下的最大单边贡献值（负值取 0），
 *   同时更新全局最大路径和 = 当前节点值 + 左贡献 + 右贡献。
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

  function dfs(node: TreeNode | null): number {
    if (node === null) {
      return 0;
    }
    const leftGain = Math.max(dfs(node.left), 0);
    const rightGain = Math.max(dfs(node.right), 0);

    maxSum = Math.max(maxSum, node.val + leftGain + rightGain);

    return node.val + Math.max(leftGain, rightGain);
  }

  dfs(root);
  return maxSum;
}

export { maxPathSum, TreeNode };
