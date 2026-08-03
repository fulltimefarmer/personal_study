/**
 * 考点：树、DFS、二叉树、前缀和
 * 题目：Path Sum III（路径总和III）
 * 题目描述：求二叉树中路径和等于 targetSum 的路径数（路径必须向下）
 * 思路：前缀和 + 哈希表。DFS 维护根到当前节点的路径和 curSum，
 *       在哈希表中查找 curSum - targetSum 的出现次数。
 *       回溯时从哈希表移除当前路径和。
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

function pathSum(root: TreeNode | null, targetSum: number): number {
    const prefixCount = new Map<number, number>();
    prefixCount.set(0, 1);

    function dfs(node: TreeNode | null, curSum: number): number {
        if (node === null) return 0;

        curSum += node.val;
        let count = prefixCount.get(curSum - targetSum) || 0;

        prefixCount.set(curSum, (prefixCount.get(curSum) || 0) + 1);

        count += dfs(node.left, curSum);
        count += dfs(node.right, curSum);

        prefixCount.set(curSum, prefixCount.get(curSum)! - 1);

        return count;
    }

    return dfs(root, 0);
}

export { pathSum, TreeNode };
