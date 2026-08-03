/**
 * 考点：树、DFS、BFS、二叉树
 * 题目：Path Sum（路径总和）
 * 题目描述：判断二叉树中是否存在从根节点到叶子节点的路径，使路径上所有节点值相加等于 targetSum。
 *   叶子节点是没有子节点的节点。
 *   示例：root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22 → true
 * 思路：DFS 递归。到达叶子节点时检查剩余和是否为当前节点值；否则递归左右子树。
 * 时间复杂度：O(n)
 * 空间复杂度：O(h)，h 为树的高度
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
  if (root === null) {
    return false;
  }
  if (root.left === null && root.right === null) {
    return root.val === targetSum;
  }
  return (
    hasPathSum(root.left, targetSum - root.val) ||
    hasPathSum(root.right, targetSum - root.val)
  );
}

export { hasPathSum, TreeNode };
