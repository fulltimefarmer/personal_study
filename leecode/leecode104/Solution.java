import java.util.*;

/**
 * 考点：Tree, DFS, Recursion
 * 题目：Maximum Depth of Binary Tree
 * 题目描述：
 * 给定一个二叉树 root，返回其最大深度。
 *
 * 二叉树的最大深度是指从根节点到最远叶子节点的最长路径上的节点数。
 *
 * 示例 1：
 * 输入：root = [3,9,20,null,null,15,7]
 * 输出：3
 * 解释：该二叉树的最大深度为 3，路径为 3 -> 20 -> 7 或 3 -> 20 -> 15。
 *
 * 示例 2：
 * 输入：root = [1,null,2]
 * 输出：2
 *
 * 提示：
 * - 树中节点的数量在 [0, 10^4] 范围内
 * - -100 <= Node.val <= 100
 *
 * 思路：
 * 1. 采用递归（深度优先搜索）自顶向下计算每个子树的最大深度。
 * 2. 递归终止条件：当前节点为空时，深度为 0。
 * 3. 分别递归计算左子树和右子树的最大深度 leftDepth 与 rightDepth。
 * 4. 当前树的最大深度 = max(leftDepth, rightDepth) + 1，加 1 表示当前节点这一层。
 * 5. 递归到叶子节点时，左右子树均为空，返回 1。
 * 数据结构/算法：递归深度优先搜索（DFS）；二叉树节点 TreeNode 含 val、left、right。
 * 时间复杂度：O(n)，每个节点访问一次
 * 空间复杂度：O(h)，递归栈空间，h 为树高
 */
class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;

    TreeNode() {}

    TreeNode(int val) {
        this.val = val;
    }

    TreeNode(int val, TreeNode left, TreeNode right) {
        this.val = val;
        this.left = left;
        this.right = right;
    }
}

public class Solution {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
    }
}
