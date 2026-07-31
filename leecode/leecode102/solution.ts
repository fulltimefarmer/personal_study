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
 *   1. 若 root 为空，直接返回空数组。
 *   2. 初始化队列 queue，将 root 入队。
 *   3. 当队列不为空时，记录当前层节点数 size，新建一个数组 level：
 *      a) 循环 size 次，出队一个节点，将其值加入 level，并将其左右子节点入队。
 *      b) 将 level 加入结果数组。
 *   4. 返回结果数组。
 * 数据结构：队列（Queue）—— 先进先出，用于按层访问节点。
 * 时间复杂度：O(n)
 * 空间复杂度：O(n)
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

function levelOrder(root: TreeNode | null): number[][] {
    const result: number[][] = [];
    if (root === null) {
        return result;
    }

    const queue: TreeNode[] = [root];
    while (queue.length > 0) {
        const size = queue.length;
        const level: number[] = [];
        for (let i = 0; i < size; i++) {
            const node = queue.shift()!;
            level.push(node.val);
            if (node.left !== null) {
                queue.push(node.left);
            }
            if (node.right !== null) {
                queue.push(node.right);
            }
        }
        result.push(level);
    }

    return result;
}
