/**
 * 考点：树、DFS、动态规划、二叉树
 * 题目：House Robber III（打家劫舍III）
 * 题目描述：二叉树排列的房屋不能同时偷相邻节点，求最大金额
 * 思路：树形 DP。DFS 返回 [rob, notRob] 两个状态。
 *       rob = node.val + left.notRob + right.notRob
 *       notRob = max(left) + max(right)
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

function rob(root: TreeNode | null): number {
    function dfs(node: TreeNode | null): [number, number] {
        if (node === null) return [0, 0];
        const left = dfs(node.left);
        const right = dfs(node.right);
        const robVal = node.val + left[1] + right[1];
        const notRob = Math.max(left[0], left[1]) + Math.max(right[0], right[1]);
        return [robVal, notRob];
    }

    const [robRoot, notRobRoot] = dfs(root);
    return Math.max(robRoot, notRobRoot);
}

export { rob, TreeNode };
