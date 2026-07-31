/**
 * 考点：Tree, BFS
 * 题目：Binary Tree Level Order Traversal
 * 题目描述：
 *   给你二叉树的根节点 root，返回其节点值的层序遍历。（即逐层地、从左到右访问所有节点）。
 *   示例 1：输入 root = [3,9,20,null,null,15,7]，输出 [[3],[9,20],[15,7]]。
 *   示例 2：输入 root = [1]，输出 [[1]]。
 *   示例 3：输入 root = []，输出 []。
 *   提示：树中节点数目在 [0, 2000] 范围内，-1000 <= Node.val <= 1000。
 * 思路：
 *   1. 若 root 为空，直接返回空列表。
 *   2. 初始化队列 queue，将 root 入队。
 *   3. 当队列不为空时，记录当前层节点数 size，新建一个列表 level：
 *      a) 循环 size 次，出队一个节点，将其值加入 level，并将其左右子节点入队。
 *      b) 将 level 加入结果列表。
 *   4. 返回结果列表。
 * 数据结构：队列（Queue）—— 先进先出，用于按层访问节点。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
 */

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

class TreeNode {
    int val;
    TreeNode left;
    TreeNode right;
    TreeNode() {}
    TreeNode(int val) { this.val = val; }
    TreeNode(int val, TreeNode left, TreeNode right) {
        this.val = val;
        this.left = left;
        this.right = right;
    }
}

public class Solution {
    public List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) {
            return result;
        }

        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        while (!queue.isEmpty()) {
            int size = queue.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode node = queue.poll();
                level.add(node.val);
                if (node.left != null) {
                    queue.offer(node.left);
                }
                if (node.right != null) {
                    queue.offer(node.right);
                }
            }
            result.add(level);
        }

        return result;
    }
}
