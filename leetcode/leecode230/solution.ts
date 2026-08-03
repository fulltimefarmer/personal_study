/**
 * 考点：树、DFS、二叉搜索树、二叉树
 * 题目：Kth Smallest Element in a BST（二叉搜索树中第 K 小的元素）
 * 题目描述：找 BST 中第 k 小的元素。root=[3,1,4,null,2],k=1 输出 1
 * 思路：迭代中序遍历（栈），到第 k 个出队元素时返回。
 * 时间复杂度：O(h + k)，h 为树高
 * 空间复杂度：O(h)
 */

class TreeNode230 {
    val: number;
    left: TreeNode230 | null;
    right: TreeNode230 | null;
    constructor(val?: number, left?: TreeNode230 | null, right?: TreeNode230 | null) {
        this.val = val === undefined ? 0 : val;
        this.left = left === undefined ? null : left;
        this.right = right === undefined ? null : right;
    }
}

function kthSmallest(root: TreeNode230 | null, k: number): number {
    const stack: TreeNode230[] = [];
    let node: TreeNode230 | null = root;

    while (true) {
        while (node !== null) {
            stack.push(node);
            node = node.left;
        }
        node = stack.pop()!;
        k--;
        if (k === 0) return node.val;
        node = node.right;
    }
}
export { kthSmallest, TreeNode230 };
