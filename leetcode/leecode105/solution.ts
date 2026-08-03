/**
 * 考点：Tree, Array, Hash Table, Divide and Conquer, Binary Tree
 * 题目：Construct Binary Tree from Preorder and Inorder Traversal（从前序与中序遍历序列构造二叉树）
 * 题目描述：给定前序遍历 preorder 和中序遍历 inorder，构造并返回二叉树根节点。
 * 示例：preorder = [3,9,20,15,7], inorder = [9,3,15,20,7] → [3,9,20,null,null,15,7]
 * 思路：递归分治。前序首元素为根，在中序中找到根位置，左侧为左子树，右侧为右子树。
 *       哈希表快速定位中序中的根索引，根据左子树大小切分前序数组，递归构造。
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

function buildTree(preorder: number[], inorder: number[]): TreeNode | null {
    const inorderMap = new Map<number, number>();
    for (let i = 0; i < inorder.length; i++) {
        inorderMap.set(inorder[i], i);
    }

    function build(preStart: number, preEnd: number, inStart: number, inEnd: number): TreeNode | null {
        if (preStart > preEnd) return null;

        const rootVal = preorder[preStart];
        const root = new TreeNode(rootVal);
        const rootIndex = inorderMap.get(rootVal)!;
        const leftSize = rootIndex - inStart;

        root.left = build(preStart + 1, preStart + leftSize, inStart, rootIndex - 1);
        root.right = build(preStart + leftSize + 1, preEnd, rootIndex + 1, inEnd);

        return root;
    }

    return build(0, preorder.length - 1, 0, inorder.length - 1);
}

export { buildTree, TreeNode };
