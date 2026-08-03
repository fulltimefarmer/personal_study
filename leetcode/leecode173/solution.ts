/**
 * 考点：栈、树、设计、二叉搜索树、二叉树、迭代器
 * 题目：Binary Search Tree Iterator（二叉搜索树迭代器）
 * 题目描述：实现 BST 的中序迭代器，支持 next() 返回下一个最小值，hasNext() 判断是否有下一个。
 * 思路：用栈模拟中序遍历。初始化时沿左子树压栈，next() 弹出栈顶并处理其右子树的左链。均摊 O(1)，空间 O(h)。
 * 时间复杂度：均摊 O(1)
 * 空间复杂度：O(h)，h 为树高
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

class BSTIterator {
    private stack: TreeNode[];

    constructor(root: TreeNode | null) {
        this.stack = [];
        this.pushLeft(root);
    }

    private pushLeft(node: TreeNode | null): void {
        while (node !== null) {
            this.stack.push(node);
            node = node.left;
        }
    }

    next(): number {
        const node = this.stack.pop()!;
        this.pushLeft(node.right);
        return node.val;
    }

    hasNext(): boolean {
        return this.stack.length > 0;
    }
}

export { BSTIterator, TreeNode };
