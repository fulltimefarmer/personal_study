/**
 * 考点：树、二叉搜索树、数组、分治、二叉树
 * 题目：Convert Sorted Array to Binary Search Tree（将有序数组转换为二叉搜索树）
 * 题目描述：将一个升序排列的整数数组转换为一棵高度平衡的二叉搜索树。
 *   高度平衡：每个节点的左右子树高度差的绝对值不超过 1。
 *   示例：nums = [-10,-3,0,5,9] → [0,-3,9,-10,null,5]
 * 思路：二分法 + 递归。每次取中间元素作为根节点，递归构建左右子树。
 * 时间复杂度：O(n)
 * 空间复杂度：O(log n)
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

function sortedArrayToBST(nums: number[]): TreeNode | null {
  function build(left: number, right: number): TreeNode | null {
    if (left > right) {
      return null;
    }
    const mid = Math.floor((left + right) / 2);
    const root = new TreeNode(nums[mid]);
    root.left = build(left, mid - 1);
    root.right = build(mid + 1, right);
    return root;
  }
  return build(0, nums.length - 1);
}

export { sortedArrayToBST, TreeNode };
