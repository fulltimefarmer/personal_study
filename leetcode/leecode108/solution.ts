/**
 * 考点：Tree, BST, Divide and Conquer, Binary Tree
 * 题目：Convert Sorted Array to Binary Search Tree（将有序数组转换为二叉搜索树）
 * 题目描述：将一个按照升序排列的有序数组，转换为一棵高度平衡的二叉搜索树。
 * "高度平衡" 二叉树是指每个节点的左右两个子树的高度差的绝对值不超过 1。
 * 示例 1：输入 nums = [-10,-3,0,5,9]，输出 [0,-3,9,-10,null,5]
 * 示例 2：输入 nums = [1,3]，输出 [3,1]
 * 思路：每次选取数组中间元素作为根节点，递归构建左右子树。
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
    function helper(left: number, right: number): TreeNode | null {
        if (left > right) return null;
        const mid = Math.floor((left + right) / 2);
        const root = new TreeNode(nums[mid]);
        root.left = helper(left, mid - 1);
        root.right = helper(mid + 1, right);
        return root;
    }
    return helper(0, nums.length - 1);
}

export { sortedArrayToBST, TreeNode };
